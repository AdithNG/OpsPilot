from app.schemas.chat import Citation
from app.core.storage import storage
from app.services.embeddings import embeddings_provider


class RetrievalService:
    async def retrieve(self, query: str) -> list[Citation]:
        query_embedding = embeddings_provider.embed_query(query)
        return storage.documents.search(query=query, query_embedding=query_embedding)
