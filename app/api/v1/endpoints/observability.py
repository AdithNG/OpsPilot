from fastapi import APIRouter

from app.core.storage import storage
from app.schemas.observability import ObservabilitySummary

router = APIRouter()


@router.get("/summary", response_model=ObservabilitySummary)
async def get_observability_summary() -> ObservabilitySummary:
    return ObservabilitySummary(
        storage_backend=storage.backend,
        document_count=storage.documents.count(),
        conversation_count=storage.conversations.count(),
        trace_count=storage.traces.count(),
        approval_count=storage.approvals.count(),
        recent_traces=storage.traces.list_recent(limit=5),
    )
