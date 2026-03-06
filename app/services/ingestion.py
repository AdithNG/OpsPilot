from app.schemas.documents import DocumentIngestRequest, DocumentIngestResponse
from app.services.document_store import document_store


class IngestionService:
    async def ingest(self, request: DocumentIngestRequest) -> DocumentIngestResponse:
        document_id, chunks_created = document_store.ingest(
            title=request.title,
            content=request.content,
            source_url=str(request.source_url) if request.source_url else None,
        )
        return DocumentIngestResponse(
            document_id=document_id,
            status="queued",
            chunks_created=chunks_created,
        )
