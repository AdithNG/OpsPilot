from fastapi import APIRouter, HTTPException, status

from app.schemas.approvals import ApprovalDecisionRequest, ApprovalDecisionResponse, ApprovalRecord
from app.services.approvals import ApprovalService

router = APIRouter()


@router.get("", response_model=list[ApprovalRecord])
async def list_approvals() -> list[ApprovalRecord]:
    service = ApprovalService()
    return await service.list()


@router.get("/{request_id}", response_model=ApprovalRecord)
async def get_approval(request_id: str) -> ApprovalRecord:
    service = ApprovalService()
    try:
        return await service.get(request_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


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
