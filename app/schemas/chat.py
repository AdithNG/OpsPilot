from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_id: str
    snippet: str


class ApprovalRequest(BaseModel):
    request_id: str
    action: str
    reason: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    intent: Literal["question", "incident_summary", "ticket_draft", "action_request"]
    citations: list[Citation] = Field(default_factory=list)
    requires_approval: bool = False
    approval: ApprovalRequest | None = None
