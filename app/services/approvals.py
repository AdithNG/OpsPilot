from app.schemas.approvals import ApprovalDecisionRequest, ApprovalDecisionResponse

_approval_store: dict[str, str] = {}


class ApprovalService:
    def reset(self) -> None:
        _approval_store.clear()

    async def create(self, action: str) -> str:
        request_id = f"approval-{len(_approval_store) + 1}"
        _approval_store[request_id] = action
        return request_id

    async def decide(
        self,
        request_id: str,
        decision: ApprovalDecisionRequest,
    ) -> ApprovalDecisionResponse:
        if request_id not in _approval_store:
            raise KeyError("Approval request not found")

        status = "approved" if decision.approved else "rejected"
        return ApprovalDecisionResponse(
            request_id=request_id,
            status=status,
            reviewer=decision.reviewer,
        )
