from typing import Literal

from pydantic import BaseModel


JobStatus = Literal["queued", "running", "completed", "failed"]
JobType = Literal["document_ingest", "github_ingest"]


class IngestionJobRecord(BaseModel):
    job_id: str
    job_type: JobType
    status: JobStatus
    source_kind: str
    document_id: str | None = None
    chunks_created: int = 0
    error_message: str | None = None
