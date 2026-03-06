from typing import Literal

from pydantic import BaseModel, Field


class TraceEvaluation(BaseModel):
    trace_id: str
    intent: Literal["question", "incident_summary", "ticket_draft", "action_request"]
    score: float
    passed: bool
    checks: list[str] = Field(default_factory=list)


class EvaluationSummary(BaseModel):
    total_traces: int
    passed_traces: int
    average_score: float
    evaluations: list[TraceEvaluation] = Field(default_factory=list)
