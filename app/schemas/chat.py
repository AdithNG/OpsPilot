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


class IncidentActionItem(BaseModel):
    owner: str
    action: str
    priority: Literal["low", "medium", "high"]


class IncidentSummary(BaseModel):
    title: str
    impact: str
    severity: Literal["sev1", "sev2", "sev3"]
    suspected_cause: str
    next_steps: list[IncidentActionItem] = Field(default_factory=list)


class TicketDraft(BaseModel):
    title: str
    summary: str
    impact: str
    reproduction_steps: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    message: str
    intent: Literal["question", "incident_summary", "ticket_draft", "action_request"]
    citations: list[Citation] = Field(default_factory=list)
    requires_approval: bool = False
    approval: ApprovalRequest | None = None
    incident_summary: IncidentSummary | None = None
    ticket_draft: TicketDraft | None = None
