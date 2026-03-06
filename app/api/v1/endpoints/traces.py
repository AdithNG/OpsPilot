from fastapi import APIRouter, HTTPException, status

from app.core.storage import storage
from app.schemas.chat import WorkflowTrace

router = APIRouter()


@router.get("/{trace_id}", response_model=WorkflowTrace)
async def get_trace(trace_id: str) -> WorkflowTrace:
    trace = storage.traces.get(trace_id)
    if trace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")
    return trace
