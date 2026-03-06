from pydantic import BaseModel, Field, HttpUrl


class DocumentIngestRequest(BaseModel):
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source_url: HttpUrl | None = None


class DocumentIngestResponse(BaseModel):
    document_id: str
    status: str
    chunks_created: int
