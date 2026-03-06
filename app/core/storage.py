from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.repositories.memory import (
    MemoryApprovalRepository,
    MemoryConversationRepository,
    MemoryDocumentRepository,
    MemoryIngestionJobRepository,
    MemoryToolExecutionRepository,
    MemoryTraceRepository,
)
from app.repositories.postgres import (
    PostgresApprovalRepository,
    PostgresConversationRepository,
    PostgresDocumentRepository,
    PostgresIngestionJobRepository,
    PostgresToolExecutionRepository,
    PostgresTraceRepository,
)


@dataclass(slots=True)
class StorageContainer:
    documents: MemoryDocumentRepository | PostgresDocumentRepository
    approvals: MemoryApprovalRepository | PostgresApprovalRepository
    conversations: MemoryConversationRepository | PostgresConversationRepository
    traces: MemoryTraceRepository | PostgresTraceRepository
    tools: MemoryToolExecutionRepository | PostgresToolExecutionRepository
    ingestion_jobs: MemoryIngestionJobRepository | PostgresIngestionJobRepository
    backend: str

    def initialize(self) -> None:
        for repository in (self.documents, self.approvals, self.conversations, self.traces, self.tools, self.ingestion_jobs):
            initialize = getattr(repository, "initialize", None)
            if callable(initialize):
                initialize()
        seed_defaults = getattr(self.documents, "seed_defaults", None)
        if callable(seed_defaults):
            seed_defaults()

    def reset(self) -> None:
        self.documents.reset()
        self.approvals.reset()
        self.conversations.reset()
        self.traces.reset()
        self.tools.reset()
        self.ingestion_jobs.reset()


def create_storage_container() -> StorageContainer:
    if settings.storage_backend == "postgres":
        return StorageContainer(
            documents=PostgresDocumentRepository(settings.database_url),
            approvals=PostgresApprovalRepository(settings.database_url),
            conversations=PostgresConversationRepository(settings.database_url),
            traces=PostgresTraceRepository(settings.database_url),
            tools=PostgresToolExecutionRepository(settings.database_url),
            ingestion_jobs=PostgresIngestionJobRepository(settings.database_url),
            backend="postgres",
        )
    return StorageContainer(
        documents=MemoryDocumentRepository(),
        approvals=MemoryApprovalRepository(),
        conversations=MemoryConversationRepository(),
        traces=MemoryTraceRepository(),
        tools=MemoryToolExecutionRepository(),
        ingestion_jobs=MemoryIngestionJobRepository(),
        backend="memory",
    )


storage = create_storage_container()
