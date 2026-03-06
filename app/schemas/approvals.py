from typing import Literal

from pydantic import BaseModel, Field

ApprovalStatus = Literal["pending", "approved", "rejected"]


class ApprovalRecord(BaseModel):
    request_id: str
    action: str
    status: ApprovalStatus
    reviewer: str | None = None
    note: str | None = None


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    reviewer: str = Field(min_length=1)
    note: str | None = None


class ApprovalDecisionResponse(ApprovalRecord):
    reviewer: str
