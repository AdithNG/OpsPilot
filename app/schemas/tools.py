from typing import Literal

from pydantic import BaseModel, Field


ToolStatus = Literal["queued", "running", "completed", "blocked", "failed"]


class ToolExecutionRequest(BaseModel):
    conversation_id: str | None = None
    tool_name: str
    input_text: str = Field(min_length=1)


class ToolExecution(BaseModel):
    execution_id: str
    conversation_id: str
    tool_name: str
    status: ToolStatus
    input_text: str
    output_text: str
    metadata: dict[str, str] = Field(default_factory=dict)
