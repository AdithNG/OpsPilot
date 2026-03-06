from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Iterable
from uuid import uuid4

from app.schemas.chat import Citation


@dataclass(slots=True)
class StoredChunk:
    document_id: str
    title: str
    content: str
    source_url: str | None


class DocumentStore:
    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self._lock = Lock()
        self._chunks: list[StoredChunk] = []
        self._seed_defaults()

    def reset(self) -> None:
        with self._lock:
            self._chunks.clear()
            self._seed_defaults()

    def ingest(self, title: str, content: str, source_url: str | None = None) -> tuple[str, int]:
        document_id = f"doc-{uuid4()}"
        chunks = [
            StoredChunk(
                document_id=document_id,
                title=title,
                content=chunk,
                source_url=source_url,
            )
            for chunk in self._chunk_content(content)
        ]
        with self._lock:
            self._chunks.extend(chunks)
        return document_id, len(chunks)

    def search(self, query: str, limit: int = 3) -> list[Citation]:
        query_terms = self._tokenize(query)
        scored = []
        with self._lock:
            for chunk in self._chunks:
                haystack = f"{chunk.title} {chunk.content}"
                score = self._score(query_terms, haystack)
                if score <= 0:
                    continue
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        citations = []
        for _, chunk in scored[:limit]:
            citations.append(
                Citation(
                    source_id=chunk.document_id,
                    snippet=chunk.content[:240],
                )
            )
        return citations

    def _seed_defaults(self) -> None:
        default_content = (
            "Deployment rollback runbook: pause deploys, restore the last known good version, "
            "verify health checks, and communicate status to stakeholders."
        )
        self._chunks.append(
            StoredChunk(
                document_id="runbook-rollback",
                title="Deployment Rollback Runbook",
                content=default_content,
                source_url="https://example.com/runbook",
            )
        )

    def _chunk_content(self, content: str) -> Iterable[str]:
        return [content[index : index + self.chunk_size] for index in range(0, len(content), self.chunk_size)] or [content]

    def _score(self, query_terms: set[str], haystack: str) -> int:
        haystack_terms = self._tokenize(haystack)
        return len(query_terms & haystack_terms)

    def _tokenize(self, text: str) -> set[str]:
        normalized = "".join(character.lower() if character.isalnum() else " " for character in text)
        return {term for term in normalized.split() if len(term) > 2}


document_store = DocumentStore()
