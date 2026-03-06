from app.schemas.chat import ApprovalRequest, ChatRequest, ChatResponse
from app.services.approvals import ApprovalService
from app.services.retrieval import RetrievalService


class WorkflowService:
    def __init__(self) -> None:
        self.retrieval = RetrievalService()
        self.approvals = ApprovalService()

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        intent = self._classify(request.message)
        citations = await self.retrieval.retrieve(request.message)

        if intent == "action_request":
            action = "Create or modify an external system record"
            request_id = await self.approvals.create(action)
            return ChatResponse(
                message="This request needs approval before any write-like action is executed.",
                intent=intent,
                citations=citations,
                requires_approval=True,
                approval=ApprovalRequest(
                    request_id=request_id,
                    action=action,
                    reason="Requested action could change external system state.",
                ),
            )

        if intent == "incident_summary":
            return ChatResponse(
                message="Incident summary: customer impact identified, remediation steps listed, and follow-up owners should be assigned.",
                intent=intent,
                citations=citations,
            )

        if intent == "ticket_draft":
            return ChatResponse(
                message="Bug ticket draft: title, impact, reproduction notes, and next action items are ready for review.",
                intent=intent,
                citations=citations,
            )

        if citations:
            return ChatResponse(
                message="The deployment runbook recommends pausing deploys, restoring the last known good version, and verifying health checks.",
                intent=intent,
                citations=citations,
            )

        return ChatResponse(
            message="I can help with runbooks, incident summaries, and drafting structured follow-up actions.",
            intent=intent,
            citations=citations,
        )

    def _classify(self, message: str) -> str:
        lowered = message.lower()
        # Write-like intents must win over content-shape hints such as "ticket".
        if any(keyword in lowered for keyword in ("create", "update", "delete", "open jira", "file ticket")):
            return "action_request"
        if any(keyword in lowered for keyword in ("draft", "bug ticket", "ticket")):
            return "ticket_draft"
        if any(keyword in lowered for keyword in ("incident", "postmortem", "outage", "logs")):
            return "incident_summary"
        return "question"
