from fastapi import APIRouter, HTTPException, status

from app.schemas.approvals import ApprovalDecisionRequest, ApprovalDecisionResponse
from app.services.approvals import ApprovalService

router = APIRouter()


@router.post("/{request_id}/decision", response_model=ApprovalDecisionResponse)
async def submit_approval_decision(
    request_id: str,
    request: ApprovalDecisionRequest,
) -> ApprovalDecisionResponse:
    service = ApprovalService()
    try:
        return await service.decide(request_id=request_id, decision=request)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
