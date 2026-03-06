from typing import Literal

from pydantic import BaseModel, Field


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    reviewer: str = Field(min_length=1)
    note: str | None = None


class ApprovalDecisionResponse(BaseModel):
    request_id: str
    status: Literal["approved", "rejected"]
    reviewer: str
