from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator


class DocumentIngestRequest(BaseModel):
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source_url: HttpUrl | None = None


class DocumentIngestResponse(BaseModel):
    document_id: str
    status: str
    chunks_created: int


class GitHubIngestRequest(BaseModel):
    owner: str = Field(min_length=1)
    repo: str = Field(min_length=1)
    artifact_type: Literal["file", "commit", "pull_request"]
    ref: str = "main"
    path: str | None = None
    commit_sha: str | None = None
    pull_request_number: int | None = None

    @model_validator(mode="after")
    def validate_required_fields(self) -> "GitHubIngestRequest":
        if self.artifact_type == "file" and not self.path:
            raise ValueError("path is required for file artifacts")
        if self.artifact_type == "commit" and not self.commit_sha:
            raise ValueError("commit_sha is required for commit artifacts")
        if self.artifact_type == "pull_request" and self.pull_request_number is None:
            raise ValueError("pull_request_number is required for pull_request artifacts")
        return self
