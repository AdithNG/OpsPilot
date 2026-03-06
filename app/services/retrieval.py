from app.schemas.chat import Citation
from app.core.storage import storage


class RetrievalService:
    async def retrieve(self, query: str) -> list[Citation]:
        return storage.documents.search(query=query)
