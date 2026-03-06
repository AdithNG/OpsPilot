from app.core.storage import storage
from app.schemas.chat import WorkflowTrace
from app.schemas.evals import EvaluationSummary, TraceEvaluation


class EvaluationService:
    def evaluate_trace(self, trace_id: str) -> TraceEvaluation | None:
        trace = storage.traces.get(trace_id)
        if trace is None:
            return None
        return self._score_trace(trace)

    def summarize_recent(self, limit: int = 10) -> EvaluationSummary:
        traces = storage.traces.list_recent(limit=limit)
        evaluations = [self._score_trace(trace) for trace in traces]
        total = len(evaluations)
        passed = sum(1 for evaluation in evaluations if evaluation.passed)
        average = round(sum(evaluation.score for evaluation in evaluations) / total, 3) if total else 0.0
        return EvaluationSummary(
            total_traces=total,
            passed_traces=passed,
            average_score=average,
            evaluations=evaluations,
        )

    def _score_trace(self, trace: WorkflowTrace) -> TraceEvaluation:
        expected_last_step = {
            "question": "respond_question",
            "incident_summary": "summarize_incident",
            "ticket_draft": "draft_ticket",
            "action_request": "gate_action",
        }[trace.intent]
        checks: list[str] = []
        score = 0.0

        if "classify" in trace.steps:
            checks.append("includes classify step")
            score += 0.25
        if "retrieve" in trace.steps:
            checks.append("includes retrieval step")
            score += 0.25
        if trace.steps and trace.steps[-1] == expected_last_step:
            checks.append(f"terminates at expected node: {expected_last_step}")
            score += 0.35
        if trace.intent != "action_request" or trace.requires_approval:
            checks.append("approval behavior matches intent")
            score += 0.15

        final_score = round(score, 3)
        return TraceEvaluation(
            trace_id=trace.trace_id,
            intent=trace.intent,
            score=final_score,
            passed=final_score >= 0.85,
            checks=checks,
        )
