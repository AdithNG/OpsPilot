from app.schemas.approvals import ApprovalDecisionRequest, ApprovalDecisionResponse, ApprovalRecord
from app.core.storage import storage


class ApprovalService:
    def reset(self) -> None:
        storage.approvals.reset()

    async def create(self, action: str) -> str:
        return storage.approvals.create(action)

    async def get(self, request_id: str) -> ApprovalRecord:
        record = storage.approvals.get(request_id)
        if record is None:
            raise KeyError("Approval request not found")
        return record

    async def list(self) -> list[ApprovalRecord]:
        return storage.approvals.list()

    async def decide(
        self,
        request_id: str,
        decision: ApprovalDecisionRequest,
    ) -> ApprovalDecisionResponse:
        record = storage.approvals.decide(
            request_id=request_id,
            approved=decision.approved,
            reviewer=decision.reviewer,
            note=decision.note,
        )
        if record is None:
            raise KeyError("Approval request not found")
        return ApprovalDecisionResponse(
            request_id=record.request_id,
            action=record.action,
            status=record.status,
            reviewer=decision.reviewer,
            note=record.note,
        )
