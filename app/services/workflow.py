from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from app.schemas.chat import (
    ApprovalRequest,
    ChatRequest,
    ChatResponse,
    Citation,
    IncidentActionItem,
    IncidentSummary,
    TicketDraft,
)
from app.core.storage import storage
from app.services.approvals import ApprovalService
from app.services.retrieval import RetrievalService

Intent = Literal["question", "incident_summary", "ticket_draft", "action_request"]


class WorkflowState(TypedDict, total=False):
    conversation_id: str
    message: str
    intent: Intent
    citations: list[Citation]
    response_message: str
    requires_approval: bool
    approval: ApprovalRequest | None
    incident_summary: IncidentSummary | None
    ticket_draft: TicketDraft | None
    trace_steps: list[str]


class WorkflowService:
    def __init__(self) -> None:
        self.retrieval = RetrievalService()
        self.approvals = ApprovalService()
        self.graph = self._build_graph()

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        conversation_id = storage.conversations.ensure(request.conversation_id)
        storage.conversations.append(conversation_id, "user", request.message)
        initial_state: WorkflowState = {
            "conversation_id": conversation_id,
            "message": request.message,
            "citations": [],
            "requires_approval": False,
            "approval": None,
            "incident_summary": None,
            "ticket_draft": None,
            "trace_steps": [],
        }
        result = await self.graph.ainvoke(initial_state)
        trace = storage.traces.create(
            conversation_id=conversation_id,
            intent=result["intent"],
            steps=result.get("trace_steps", []),
            requires_approval=result.get("requires_approval", False),
        )
        storage.conversations.append(conversation_id, "assistant", result["response_message"])
        return ChatResponse(
            conversation_id=conversation_id,
            message=result["response_message"],
            intent=result["intent"],
            citations=result.get("citations", []),
            requires_approval=result.get("requires_approval", False),
            approval=result.get("approval"),
            incident_summary=result.get("incident_summary"),
            ticket_draft=result.get("ticket_draft"),
            trace=trace,
        )

    def _build_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("classify", self._classify_request)
        graph.add_node("retrieve", self._retrieve_context)
        graph.add_node("respond_question", self._respond_question)
        graph.add_node("summarize_incident", self._summarize_incident)
        graph.add_node("draft_ticket", self._draft_ticket)
        graph.add_node("gate_action", self._gate_action)

        graph.add_edge(START, "classify")
        graph.add_edge("classify", "retrieve")
        graph.add_conditional_edges(
            "retrieve",
            self._route_by_intent,
            {
                "question": "respond_question",
                "incident_summary": "summarize_incident",
                "ticket_draft": "draft_ticket",
                "action_request": "gate_action",
            },
        )
        graph.add_edge("respond_question", END)
        graph.add_edge("summarize_incident", END)
        graph.add_edge("draft_ticket", END)
        graph.add_edge("gate_action", END)
        return graph.compile()

    async def _classify_request(self, state: WorkflowState) -> WorkflowState:
        return {"intent": self._classify(state["message"]), "trace_steps": [*state.get("trace_steps", []), "classify"]}

    async def _retrieve_context(self, state: WorkflowState) -> WorkflowState:
        citations = await self.retrieval.retrieve(state["message"])
        return {"citations": citations, "trace_steps": [*state.get("trace_steps", []), "retrieve"]}

    async def _respond_question(self, state: WorkflowState) -> WorkflowState:
        citations = state.get("citations", [])
        if citations:
            return {
                "response_message": f"Relevant guidance: {citations[0].snippet}",
                "trace_steps": [*state.get("trace_steps", []), "respond_question"],
            }
        return {
            "response_message": "I can help with runbooks, incident summaries, and drafting structured follow-up actions.",
            "trace_steps": [*state.get("trace_steps", []), "respond_question"],
        }

    async def _summarize_incident(self, state: WorkflowState) -> WorkflowState:
        summary = IncidentSummary(
            title="Production incident follow-up",
            impact="Customer-facing errors were detected and require verification of recovery.",
            severity="sev2",
            suspected_cause="A recent deploy or dependent service regression should be investigated first.",
            next_steps=[
                IncidentActionItem(
                    owner="oncall-engineer",
                    action="Confirm customer impact window and affected systems.",
                    priority="high",
                ),
                IncidentActionItem(
                    owner="service-owner",
                    action="Validate rollback state and document root-cause evidence.",
                    priority="high",
                ),
            ],
        )
        return {
            "response_message": (
                "Incident summary: impact is identified, likely cause is captured, and next actions should be assigned "
                "to an owner with a due date."
            ),
            "incident_summary": summary,
            "trace_steps": [*state.get("trace_steps", []), "summarize_incident"],
        }

    async def _draft_ticket(self, state: WorkflowState) -> WorkflowState:
        citations = state.get("citations", [])
        grounding = f" Relevant context: {citations[0].snippet}" if citations else ""
        draft = TicketDraft(
            title="Investigate production issue after deploy",
            summary="Users are experiencing a production issue that needs triage and a concrete fix plan.",
            impact="The issue affects normal user workflows and should be prioritized for engineering follow-up.",
            reproduction_steps=[
                "Identify the failing workflow or endpoint.",
                "Compare behavior before and after the latest deploy.",
                "Capture logs, metrics, and any error responses.",
            ],
            acceptance_criteria=[
                "Root cause is identified and documented.",
                "A fix is verified in the target environment.",
                "Monitoring confirms the issue no longer reproduces.",
            ],
        )
        return {
            "response_message": (
                "Bug ticket draft: include title, customer impact, reproduction notes, expected behavior, "
                f"and acceptance criteria.{grounding}"
            ),
            "ticket_draft": draft,
            "trace_steps": [*state.get("trace_steps", []), "draft_ticket"],
        }

    async def _gate_action(self, state: WorkflowState) -> WorkflowState:
        action = "Create or modify an external system record"
        request_id = await self.approvals.create(action)
        return {
            "response_message": "This request needs approval before any write-like action is executed.",
            "requires_approval": True,
            "approval": ApprovalRequest(
                request_id=request_id,
                action=action,
                reason="Requested action could change external system state.",
            ),
            "trace_steps": [*state.get("trace_steps", []), "gate_action"],
        }

    def _route_by_intent(self, state: WorkflowState) -> Intent:
        return state["intent"]

    def _classify(self, message: str) -> Intent:
        lowered = message.lower()
        if any(keyword in lowered for keyword in ("create", "update", "delete", "open jira", "file ticket")):
            return "action_request"
        if any(keyword in lowered for keyword in ("draft", "bug ticket", "ticket")):
            return "ticket_draft"
        if any(keyword in lowered for keyword in ("incident", "postmortem", "outage", "logs")):
            return "incident_summary"
        return "question"
