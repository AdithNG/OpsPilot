from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.evals import EvaluationSummary, TraceEvaluation
from app.services.evals import EvaluationService

router = APIRouter()


@router.get("/summary", response_model=EvaluationSummary)
async def get_eval_summary(limit: int = Query(default=10, ge=1, le=50)) -> EvaluationSummary:
    service = EvaluationService()
    return service.summarize_recent(limit=limit)


@router.get("/traces/{trace_id}", response_model=TraceEvaluation)
async def evaluate_trace(trace_id: str) -> TraceEvaluation:
    service = EvaluationService()
    evaluation = service.evaluate_trace(trace_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    return evaluation
