from app.schemas.approvals import ApprovalDecisionRequest, ApprovalDecisionResponse
from app.core.storage import storage


class ApprovalService:
    def reset(self) -> None:
        storage.approvals.reset()

    async def create(self, action: str) -> str:
        return storage.approvals.create(action)

    async def decide(
        self,
        request_id: str,
        decision: ApprovalDecisionRequest,
    ) -> ApprovalDecisionResponse:
        if not storage.approvals.exists(request_id):
            raise KeyError("Approval request not found")

        status = "approved" if decision.approved else "rejected"
        return ApprovalDecisionResponse(
            request_id=request_id,
            status=status,
            reviewer=decision.reviewer,
        )
