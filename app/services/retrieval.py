from app.schemas.chat import Citation
from app.services.document_store import document_store


class RetrievalService:
    async def retrieve(self, query: str) -> list[Citation]:
        return document_store.search(query=query)
