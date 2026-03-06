from pydantic import BaseModel, Field

from app.schemas.chat import WorkflowTrace


class ObservabilitySummary(BaseModel):
    storage_backend: str
    document_count: int
    conversation_count: int
    trace_count: int
    approval_count: int
    recent_traces: list[WorkflowTrace] = Field(default_factory=list)
