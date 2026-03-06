from __future__ import annotations

from contextlib import closing
from uuid import uuid4

from app.schemas.chat import Citation


class PostgresDocumentRepository:
    def __init__(self, dsn: str, chunk_size: int = 500) -> None:
        self.dsn = dsn
        self.chunk_size = chunk_size

    def initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS documents (
                        document_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source_url TEXT NULL
                    )
                    """
                )
                connection.commit()
        self.seed_defaults()

    def seed_defaults(self) -> None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM documents WHERE document_id = %s", ("runbook-rollback",))
                if cursor.fetchone()[0]:
                    return
                cursor.execute(
                    """
                    INSERT INTO documents (document_id, title, content, source_url)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        "runbook-rollback",
                        "Deployment Rollback Runbook",
                        (
                            "Deployment rollback runbook: pause deploys, restore the last known good version, "
                            "verify health checks, and communicate status to stakeholders."
                        ),
                        "https://example.com/runbook",
                    ),
                )
                connection.commit()

    def reset(self) -> None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE documents")
                connection.commit()
        self.seed_defaults()

    def ingest(self, title: str, content: str, source_url: str | None = None) -> tuple[str, int]:
        document_id = f"doc-{uuid4()}"
        chunks = [content[index : index + self.chunk_size] for index in range(0, len(content), self.chunk_size)] or [content]
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                for chunk in chunks:
                    cursor.execute(
                        """
                        INSERT INTO documents (document_id, title, content, source_url)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (document_id, title, chunk, source_url),
                    )
                connection.commit()
        return document_id, len(chunks)

    def search(self, query: str, limit: int = 3) -> list[Citation]:
        query_text = " | ".join(term for term in self._tokenize(query))
        if not query_text:
            return []
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT document_id, content
                    FROM documents
                    WHERE to_tsvector('english', title || ' ' || content) @@ to_tsquery('english', %s)
                    LIMIT %s
                    """,
                    (query_text, limit),
                )
                return [Citation(source_id=document_id, snippet=content[:240]) for document_id, content in cursor.fetchall()]

    def _tokenize(self, text: str) -> list[str]:
        normalized = "".join(character.lower() if character.isalnum() else " " for character in text)
        return [term for term in normalized.split() if len(term) > 2]

    def _connect(self):
        from psycopg import connect

        return connect(self.dsn)


class PostgresApprovalRepository:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS approvals (
                        request_id TEXT PRIMARY KEY,
                        action TEXT NOT NULL
                    )
                    """
                )
                connection.commit()

    def reset(self) -> None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE approvals")
                connection.commit()

    def create(self, action: str) -> str:
        request_id = f"approval-{uuid4()}"
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO approvals (request_id, action) VALUES (%s, %s)",
                    (request_id, action),
                )
                connection.commit()
        return request_id

    def exists(self, request_id: str) -> bool:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM approvals WHERE request_id = %s", (request_id,))
                return cursor.fetchone() is not None

    def _connect(self):
        from psycopg import connect

        return connect(self.dsn)
