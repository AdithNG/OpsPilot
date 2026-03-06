from langchain_core.documents import Document

from app.schemas.documents import DocumentIngestRequest, DocumentIngestResponse
from app.core.storage import storage
from app.services.embeddings import embeddings_provider


class IngestionService:
    chunk_size = 500

    async def ingest(self, request: DocumentIngestRequest) -> DocumentIngestResponse:
        chunks = self._chunk_content(request.content)
        documents = [Document(page_content=chunk, metadata={"title": request.title}) for chunk in chunks]
        embeddings = embeddings_provider.embed_documents([document.page_content for document in documents])
        document_id, chunks_created = storage.documents.ingest(
            title=request.title,
            content=request.content,
            source_url=str(request.source_url) if request.source_url else None,
            embeddings=embeddings,
        )
        return DocumentIngestResponse(
            document_id=document_id,
            status="queued",
            chunks_created=chunks_created,
        )

    def _chunk_content(self, content: str) -> list[str]:
        return [content[index : index + self.chunk_size] for index in range(0, len(content), self.chunk_size)] or [content]
