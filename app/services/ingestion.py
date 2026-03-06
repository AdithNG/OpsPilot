import math
from uuid import uuid4

from app.schemas.documents import DocumentIngestRequest, DocumentIngestResponse


class IngestionService:
    chunk_size = 500

    async def ingest(self, request: DocumentIngestRequest) -> DocumentIngestResponse:
        chunks_created = max(1, math.ceil(len(request.content) / self.chunk_size))
        return DocumentIngestResponse(
            document_id=f"doc-{uuid4()}",
            status="queued",
            chunks_created=chunks_created,
        )
