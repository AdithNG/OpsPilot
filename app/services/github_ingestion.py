from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.schemas.documents import DocumentIngestRequest, DocumentIngestResponse, GitHubIngestRequest
from app.services.ingestion import IngestionService


@dataclass(slots=True)
class GitHubArtifact:
    title: str
    content: str
    source_url: str


class GitHubArtifactClient:
    user_agent = "OpsPilot/0.1"

    def fetch_artifact(self, request: GitHubIngestRequest) -> GitHubArtifact:
        if request.artifact_type == "file":
            return self._fetch_file(request)
        if request.artifact_type == "commit":
            return self._fetch_commit(request)
        return self._fetch_pull_request(request)

    def _fetch_file(self, request: GitHubIngestRequest) -> GitHubArtifact:
        assert request.path is not None
        raw_url = f"https://raw.githubusercontent.com/{request.owner}/{request.repo}/{request.ref}/{request.path}"
        content = self._read_text(raw_url)
        return GitHubArtifact(
            title=f"{request.repo}/{request.path}@{request.ref}",
            content=content,
            source_url=f"https://github.com/{request.owner}/{request.repo}/blob/{request.ref}/{request.path}",
        )

    def _fetch_commit(self, request: GitHubIngestRequest) -> GitHubArtifact:
        assert request.commit_sha is not None
        api_url = f"https://api.github.com/repos/{request.owner}/{request.repo}/commits/{request.commit_sha}"
        payload = self._read_json(api_url)
        files = payload.get("files", [])
        file_lines = [
            f"- {item.get('filename', 'unknown')} ({item.get('status', 'modified')}, changes={item.get('changes', 0)})"
            for item in files[:20]
        ]
        content = "\n".join(
            [
                f"Commit: {payload.get('sha', request.commit_sha)}",
                f"Author: {(payload.get('commit') or {}).get('author', {}).get('name', 'unknown')}",
                f"Message: {(payload.get('commit') or {}).get('message', '').strip()}",
                "Changed files:",
                *file_lines,
            ]
        )
        return GitHubArtifact(
            title=f"{request.repo} commit {request.commit_sha[:7]}",
            content=content,
            source_url=payload.get("html_url", api_url),
        )

    def _fetch_pull_request(self, request: GitHubIngestRequest) -> GitHubArtifact:
        assert request.pull_request_number is not None
        api_url = f"https://api.github.com/repos/{request.owner}/{request.repo}/pulls/{request.pull_request_number}"
        payload = self._read_json(api_url)
        content = "\n".join(
            [
                f"Pull request: {payload.get('title', 'Untitled PR')}",
                f"State: {payload.get('state', 'open')}",
                f"Author: {(payload.get('user') or {}).get('login', 'unknown')}",
                f"Branch: {((payload.get('head') or {}).get('ref') or 'unknown')} -> {((payload.get('base') or {}).get('ref') or 'unknown')}",
                f"Body: {(payload.get('body') or '').strip() or 'No description provided.'}",
            ]
        )
        return GitHubArtifact(
            title=f"{request.repo} PR #{request.pull_request_number}",
            content=content,
            source_url=payload.get("html_url", api_url),
        )

    def _read_text(self, url: str) -> str:
        with urlopen(self._build_request(url), timeout=10) as response:
            return response.read().decode("utf-8")

    def _read_json(self, url: str) -> dict:
        with urlopen(self._build_request(url), timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def _build_request(self, url: str) -> Request:
        return Request(url, headers={"User-Agent": self.user_agent, "Accept": "application/vnd.github+json"})


class GitHubIngestionService:
    def __init__(self, client: GitHubArtifactClient | None = None, ingestion_service: IngestionService | None = None) -> None:
        self.client = client or GitHubArtifactClient()
        self.ingestion_service = ingestion_service or IngestionService()

    async def ingest(self, request: GitHubIngestRequest) -> DocumentIngestResponse:
        artifact = self.fetch_artifact(request)
        ingest_request = DocumentIngestRequest(
            title=artifact.title,
            content=artifact.content,
            source_url=artifact.source_url,
        )
        return await self.ingestion_service.ingest(ingest_request)

    def fetch_artifact(self, request: GitHubIngestRequest) -> GitHubArtifact:
        try:
            return self.client.fetch_artifact(request)
        except HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"GitHub returned HTTP {exc.code} while fetching artifact.",
            ) from exc
        except URLError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to reach GitHub for artifact ingestion.",
            ) from exc
