from fastapi import APIRouter, status

from app.schemas.documents import DocumentIngestRequest, DocumentIngestResponse, GitHubIngestRequest
from app.services.github_ingestion import GitHubIngestionService
from app.services.ingestion import IngestionService

router = APIRouter()


@router.post("/ingest", response_model=DocumentIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(request: DocumentIngestRequest) -> DocumentIngestResponse:
    service = IngestionService()
    return await service.ingest(request)


@router.post("/ingest/github", response_model=DocumentIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_github_artifact(request: GitHubIngestRequest) -> DocumentIngestResponse:
    service = GitHubIngestionService()
    return await service.ingest(request)
