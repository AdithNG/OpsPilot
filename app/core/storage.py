from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.repositories.memory import MemoryApprovalRepository, MemoryDocumentRepository
from app.repositories.postgres import PostgresApprovalRepository, PostgresDocumentRepository


@dataclass(slots=True)
class StorageContainer:
    documents: MemoryDocumentRepository | PostgresDocumentRepository
    approvals: MemoryApprovalRepository | PostgresApprovalRepository
    backend: str

    def initialize(self) -> None:
        initialize = getattr(self.documents, "initialize", None)
        if callable(initialize):
            initialize()
        else:
            self.documents.seed_defaults()
        approval_initialize = getattr(self.approvals, "initialize", None)
        if callable(approval_initialize):
            approval_initialize()

    def reset(self) -> None:
        self.documents.reset()
        self.approvals.reset()


def create_storage_container() -> StorageContainer:
    if settings.storage_backend == "postgres":
        return StorageContainer(
            documents=PostgresDocumentRepository(settings.database_url),
            approvals=PostgresApprovalRepository(settings.database_url),
            backend="postgres",
        )
    return StorageContainer(
        documents=MemoryDocumentRepository(),
        approvals=MemoryApprovalRepository(),
        backend="memory",
    )


storage = create_storage_container()
