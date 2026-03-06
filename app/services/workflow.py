from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from app.schemas.chat import ApprovalRequest, ChatRequest, ChatResponse, Citation
from app.services.approvals import ApprovalService
from app.services.retrieval import RetrievalService

Intent = Literal["question", "incident_summary", "ticket_draft", "action_request"]


class WorkflowState(TypedDict, total=False):
    message: str
    intent: Intent
    citations: list[Citation]
    response_message: str
    requires_approval: bool
    approval: ApprovalRequest | None


class WorkflowService:
    def __init__(self) -> None:
        self.retrieval = RetrievalService()
        self.approvals = ApprovalService()
        self.graph = self._build_graph()

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        initial_state: WorkflowState = {
            "message": request.message,
            "citations": [],
            "requires_approval": False,
            "approval": None,
        }
        result = await self.graph.ainvoke(initial_state)
        return ChatResponse(
            message=result["response_message"],
            intent=result["intent"],
            citations=result.get("citations", []),
            requires_approval=result.get("requires_approval", False),
            approval=result.get("approval"),
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
        return {"intent": self._classify(state["message"])}

    async def _retrieve_context(self, state: WorkflowState) -> WorkflowState:
        citations = await self.retrieval.retrieve(state["message"])
        return {"citations": citations}

    async def _respond_question(self, state: WorkflowState) -> WorkflowState:
        citations = state.get("citations", [])
        if citations:
            return {
                "response_message": f"Relevant guidance: {citations[0].snippet}",
            }
        return {
            "response_message": "I can help with runbooks, incident summaries, and drafting structured follow-up actions.",
        }

    async def _summarize_incident(self, state: WorkflowState) -> WorkflowState:
        return {
            "response_message": (
                "Incident summary: impact is identified, likely cause is captured, and next actions should be assigned "
                "to an owner with a due date."
            )
        }

    async def _draft_ticket(self, state: WorkflowState) -> WorkflowState:
        citations = state.get("citations", [])
        grounding = f" Relevant context: {citations[0].snippet}" if citations else ""
        return {
            "response_message": (
                "Bug ticket draft: include title, customer impact, reproduction notes, expected behavior, "
                f"and acceptance criteria.{grounding}"
            )
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
