from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.schemas.documents import DocumentIngestRequest, DocumentIngestResponse, GitHubIngestRequest
from app.schemas.jobs import IngestionJobRecord
from app.services.github_ingestion import GitHubIngestionService
from app.services.ingestion import IngestionService
from app.services.jobs import IngestionJobService

router = APIRouter()


@router.post("/ingest", response_model=DocumentIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(request: DocumentIngestRequest, background_tasks: BackgroundTasks) -> DocumentIngestResponse:
    service = IngestionService()
    jobs = IngestionJobService()
    document_id = service.reserve_document_id()
    job = jobs.create(job_type="document_ingest", source_kind="document", document_id=document_id)
    background_tasks.add_task(_run_document_ingest_job, job.job_id, request, document_id)
    return DocumentIngestResponse(
        document_id=document_id,
        job_id=job.job_id,
        status=job.status,
        chunks_created=0,
    )


@router.post("/ingest/github", response_model=DocumentIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_github_artifact(request: GitHubIngestRequest, background_tasks: BackgroundTasks) -> DocumentIngestResponse:
    jobs = IngestionJobService()
    ingest_service = IngestionService()
    document_id = ingest_service.reserve_document_id()
    job = jobs.create(job_type="github_ingest", source_kind=request.artifact_type, document_id=document_id)
    background_tasks.add_task(_run_github_ingest_job, job.job_id, request, document_id)
    return DocumentIngestResponse(
        document_id=document_id,
        job_id=job.job_id,
        status=job.status,
        chunks_created=0,
    )


@router.get("/jobs", response_model=list[IngestionJobRecord])
async def list_ingestion_jobs(limit: int = Query(default=20, ge=1, le=100)) -> list[IngestionJobRecord]:
    jobs = IngestionJobService()
    return jobs.list(limit=limit)


@router.get("/jobs/{job_id}", response_model=IngestionJobRecord)
async def get_ingestion_job(job_id: str) -> IngestionJobRecord:
    jobs = IngestionJobService()
    record = jobs.get(job_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found.")
    return record


async def _run_document_ingest_job(job_id: str, request: DocumentIngestRequest, document_id: str) -> None:
    jobs = IngestionJobService()
    service = IngestionService()
    jobs.mark_running(job_id)
    try:
        result = await service.ingest(request, document_id=document_id)
    except Exception as exc:
        jobs.mark_failed(job_id, str(exc))
        return
    jobs.mark_completed(job_id, result.chunks_created)


async def _run_github_ingest_job(job_id: str, request: GitHubIngestRequest, document_id: str) -> None:
    jobs = IngestionJobService()
    github_service = GitHubIngestionService()
    jobs.mark_running(job_id)
    try:
        artifact = github_service.fetch_artifact(request)
        ingest_request = DocumentIngestRequest(
            title=artifact.title,
            content=artifact.content,
            source_url=artifact.source_url,
        )
        result = await github_service.ingestion_service.ingest(ingest_request, document_id=document_id)
    except Exception as exc:
        jobs.mark_failed(job_id, str(exc))
        return
    jobs.mark_completed(job_id, result.chunks_created)
