from app.core.storage import storage
from app.schemas.jobs import IngestionJobRecord


class IngestionJobService:
    def create(self, job_type: str, source_kind: str, document_id: str) -> IngestionJobRecord:
        return storage.ingestion_jobs.create(job_type=job_type, source_kind=source_kind, document_id=document_id)

    def get(self, job_id: str) -> IngestionJobRecord | None:
        return storage.ingestion_jobs.get(job_id)

    def list(self, limit: int = 20) -> list[IngestionJobRecord]:
        return storage.ingestion_jobs.list(limit=limit)

    def mark_running(self, job_id: str) -> IngestionJobRecord | None:
        return storage.ingestion_jobs.update(job_id, status="running")

    def mark_completed(self, job_id: str, chunks_created: int) -> IngestionJobRecord | None:
        return storage.ingestion_jobs.update(job_id, status="completed", chunks_created=chunks_created, error_message=None)

    def mark_failed(self, job_id: str, error_message: str) -> IngestionJobRecord | None:
        return storage.ingestion_jobs.update(job_id, status="failed", error_message=error_message)
