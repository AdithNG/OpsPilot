from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Iterable
from uuid import uuid4

from app.schemas.approvals import ApprovalRecord
from app.schemas.chat import Citation, ConversationMessage, WorkflowTrace


@dataclass(slots=True)
class StoredChunk:
    document_id: str
    title: str
    content: str
    source_url: str | None


class MemoryDocumentRepository:
    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size
        self._lock = Lock()
        self._chunks: list[StoredChunk] = []

    def seed_defaults(self) -> None:
        with self._lock:
            if self._chunks:
                return
            self._chunks.append(
                StoredChunk(
                    document_id="runbook-rollback",
                    title="Deployment Rollback Runbook",
                    content=(
                        "Deployment rollback runbook: pause deploys, restore the last known good version, "
                        "verify health checks, and communicate status to stakeholders."
                    ),
                    source_url="https://example.com/runbook",
                )
            )

    def reset(self) -> None:
        with self._lock:
            self._chunks.clear()
        self.seed_defaults()

    def ingest(self, title: str, content: str, source_url: str | None = None) -> tuple[str, int]:
        document_id = f"doc-{uuid4()}"
        chunks = [
            StoredChunk(document_id=document_id, title=title, content=chunk, source_url=source_url)
            for chunk in self._chunk_content(content)
        ]
        with self._lock:
            self._chunks.extend(chunks)
        return document_id, len(chunks)

    def search(self, query: str, limit: int = 3) -> list[Citation]:
        query_terms = self._tokenize(query)
        scored: list[tuple[int, StoredChunk]] = []
        with self._lock:
            for chunk in self._chunks:
                haystack = f"{chunk.title} {chunk.content}"
                score = self._score(query_terms, haystack)
                if score > 0:
                    scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [Citation(source_id=chunk.document_id, snippet=chunk.content[:240]) for _, chunk in scored[:limit]]

    def count(self) -> int:
        with self._lock:
            return len(self._chunks)

    def _chunk_content(self, content: str) -> Iterable[str]:
        return [content[index : index + self.chunk_size] for index in range(0, len(content), self.chunk_size)] or [content]

    def _score(self, query_terms: set[str], haystack: str) -> int:
        return len(query_terms & self._tokenize(haystack))

    def _tokenize(self, text: str) -> set[str]:
        normalized = "".join(character.lower() if character.isalnum() else " " for character in text)
        return {term for term in normalized.split() if len(term) > 2}


class MemoryApprovalRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._records: dict[str, ApprovalRecord] = {}
        self._order: list[str] = []

    def reset(self) -> None:
        with self._lock:
            self._records.clear()
            self._order.clear()

    def create(self, action: str) -> str:
        with self._lock:
            request_id = f"approval-{len(self._records) + 1}"
            self._records[request_id] = ApprovalRecord(
                request_id=request_id,
                action=action,
                status="pending",
            )
            self._order.append(request_id)
            return request_id

    def exists(self, request_id: str) -> bool:
        with self._lock:
            return request_id in self._records

    def get(self, request_id: str) -> ApprovalRecord | None:
        with self._lock:
            return self._records.get(request_id)

    def list(self) -> list[ApprovalRecord]:
        with self._lock:
            return [self._records[request_id] for request_id in reversed(self._order)]

    def decide(self, request_id: str, approved: bool, reviewer: str, note: str | None) -> ApprovalRecord | None:
        with self._lock:
            record = self._records.get(request_id)
            if record is None:
                return None
            updated = ApprovalRecord(
                request_id=record.request_id,
                action=record.action,
                status="approved" if approved else "rejected",
                reviewer=reviewer,
                note=note,
            )
            self._records[request_id] = updated
            return updated

    def count(self) -> int:
        with self._lock:
            return len(self._records)


class MemoryConversationRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._conversations: dict[str, list[ConversationMessage]] = {}

    def reset(self) -> None:
        with self._lock:
            self._conversations.clear()

    def ensure(self, conversation_id: str | None = None) -> str:
        with self._lock:
            actual_conversation_id = conversation_id or f"conv-{uuid4()}"
            self._conversations.setdefault(actual_conversation_id, [])
            return actual_conversation_id

    def append(self, conversation_id: str, role: str, content: str) -> None:
        with self._lock:
            self._conversations.setdefault(conversation_id, []).append(
                ConversationMessage(role=role, content=content)
            )

    def get_messages(self, conversation_id: str) -> list[ConversationMessage]:
        with self._lock:
            return list(self._conversations.get(conversation_id, []))

    def count(self) -> int:
        with self._lock:
            return len(self._conversations)


class MemoryTraceRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._traces: dict[str, WorkflowTrace] = {}
        self._order: list[str] = []

    def reset(self) -> None:
        with self._lock:
            self._traces.clear()
            self._order.clear()

    def create(
        self,
        conversation_id: str,
        intent: str,
        steps: list[str],
        requires_approval: bool,
    ) -> WorkflowTrace:
        trace = WorkflowTrace(
            trace_id=f"trace-{uuid4()}",
            conversation_id=conversation_id,
            intent=intent,
            steps=steps,
            requires_approval=requires_approval,
        )
        with self._lock:
            self._traces[trace.trace_id] = trace
            self._order.append(trace.trace_id)
        return trace

    def get(self, trace_id: str) -> WorkflowTrace | None:
        with self._lock:
            return self._traces.get(trace_id)

    def count(self) -> int:
        with self._lock:
            return len(self._traces)

    def list_recent(self, limit: int = 5) -> list[WorkflowTrace]:
        with self._lock:
            trace_ids = list(reversed(self._order[-limit:]))
            return [self._traces[trace_id] for trace_id in trace_ids]
