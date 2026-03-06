from typing import Literal

from pydantic import BaseModel, Field


ToolStatus = Literal["completed", "blocked"]


class ToolExecution(BaseModel):
    execution_id: str
    conversation_id: str
    tool_name: str
    status: ToolStatus
    input_text: str
    output_text: str
    metadata: dict[str, str] = Field(default_factory=dict)
