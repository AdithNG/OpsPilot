from __future__ import annotations

from contextlib import closing
from uuid import uuid4

from app.schemas.approvals import ApprovalRecord
from app.schemas.chat import Citation, ConversationMessage, WorkflowTrace


class PostgresDocumentRepository:
    def __init__(self, dsn: str, chunk_size: int = 500) -> None:
        self.dsn = dsn
        self.chunk_size = chunk_size

    def initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS documents (
                        document_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source_url TEXT NULL,
                        embedding vector(64) NULL
                    )
                    """
                )
                cursor.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS embedding vector(64)")
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

    def ingest(
        self,
        title: str,
        content: str,
        source_url: str | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> tuple[str, int]:
        document_id = f"doc-{uuid4()}"
        chunks = [content[index : index + self.chunk_size] for index in range(0, len(content), self.chunk_size)] or [content]
        if embeddings is None:
            embeddings = [[] for _ in chunks]
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                for chunk, embedding in zip(chunks, embeddings, strict=False):
                    cursor.execute(
                        """
                        INSERT INTO documents (document_id, title, content, source_url, embedding)
                        VALUES (%s, %s, %s, %s, %s::vector)
                        """,
                        (document_id, title, chunk, source_url, self._vector_literal(embedding)),
                    )
                connection.commit()
        return document_id, len(chunks)

    def search(self, query: str, limit: int = 3, query_embedding: list[float] | None = None) -> list[Citation]:
        query_text = " | ".join(term for term in self._tokenize(query))
        vector_literal = self._vector_literal(query_embedding or [])
        if not query_text and not query_embedding:
            return []
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT document_id, content
                    FROM documents
                    WHERE (
                        CASE
                            WHEN %s = '' THEN TRUE
                            ELSE to_tsvector('english', title || ' ' || content) @@ to_tsquery('english', %s)
                        END
                    )
                    LIMIT %s
                    """,
                    (query_text, query_text, limit),
                )
                lexical_rows = cursor.fetchall()
                if query_embedding:
                    cursor.execute(
                        """
                        SELECT document_id, content
                        FROM documents
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                        """,
                        (vector_literal, limit),
                    )
                    vector_rows = cursor.fetchall()
                else:
                    vector_rows = []
                combined: list[tuple[str, str]] = []
                seen: set[str] = set()
                for document_id, content in [*vector_rows, *lexical_rows]:
                    key = f"{document_id}:{content}"
                    if key in seen:
                        continue
                    seen.add(key)
                    combined.append((document_id, content))
                return [Citation(source_id=document_id, snippet=content[:240]) for document_id, content in combined[:limit]]

    def count(self) -> int:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM documents")
                return cursor.fetchone()[0]

    def _tokenize(self, text: str) -> list[str]:
        normalized = "".join(character.lower() if character.isalnum() else " " for character in text)
        return [term for term in normalized.split() if len(term) > 2]

    def _vector_literal(self, embedding: list[float]) -> str:
        if not embedding:
            embedding = [0.0] * 64
        return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"

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
                        action TEXT NOT NULL,
                        status TEXT NOT NULL,
                        reviewer TEXT NULL,
                        note TEXT NULL
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
                    "INSERT INTO approvals (request_id, action, status, reviewer, note) VALUES (%s, %s, %s, %s, %s)",
                    (request_id, action, "pending", None, None),
                )
                connection.commit()
        return request_id

    def exists(self, request_id: str) -> bool:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM approvals WHERE request_id = %s", (request_id,))
                return cursor.fetchone() is not None

    def get(self, request_id: str) -> ApprovalRecord | None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT request_id, action, status, reviewer, note FROM approvals WHERE request_id = %s",
                    (request_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                return ApprovalRecord(
                    request_id=row[0],
                    action=row[1],
                    status=row[2],
                    reviewer=row[3],
                    note=row[4],
                )

    def list(self) -> list[ApprovalRecord]:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT request_id, action, status, reviewer, note
                    FROM approvals
                    ORDER BY request_id DESC
                    """
                )
                return [
                    ApprovalRecord(
                        request_id=request_id,
                        action=action,
                        status=status,
                        reviewer=reviewer,
                        note=note,
                    )
                    for request_id, action, status, reviewer, note in cursor.fetchall()
                ]

    def decide(self, request_id: str, approved: bool, reviewer: str, note: str | None) -> ApprovalRecord | None:
        status = "approved" if approved else "rejected"
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE approvals
                    SET status = %s, reviewer = %s, note = %s
                    WHERE request_id = %s
                    RETURNING request_id, action, status, reviewer, note
                    """,
                    (status, reviewer, note, request_id),
                )
                row = cursor.fetchone()
                connection.commit()
                if row is None:
                    return None
                return ApprovalRecord(
                    request_id=row[0],
                    action=row[1],
                    status=row[2],
                    reviewer=row[3],
                    note=row[4],
                )

    def count(self) -> int:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM approvals")
                return cursor.fetchone()[0]

    def _connect(self):
        from psycopg import connect

        return connect(self.dsn)


class PostgresConversationRepository:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversations (
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
                connection.commit()

    def reset(self) -> None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE conversations")
                connection.commit()

    def ensure(self, conversation_id: str | None = None) -> str:
        return conversation_id or f"conv-{uuid4()}"

    def append(self, conversation_id: str, role: str, content: str) -> None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO conversations (conversation_id, role, content)
                    VALUES (%s, %s, %s)
                    """,
                    (conversation_id, role, content),
                )
                connection.commit()

    def get_messages(self, conversation_id: str) -> list[ConversationMessage]:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT role, content
                    FROM conversations
                    WHERE conversation_id = %s
                    ORDER BY created_at ASC
                    """,
                    (conversation_id,),
                )
                return [ConversationMessage(role=role, content=content) for role, content in cursor.fetchall()]

    def count(self) -> int:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(DISTINCT conversation_id) FROM conversations")
                return cursor.fetchone()[0]

    def _connect(self):
        from psycopg import connect

        return connect(self.dsn)


class PostgresTraceRepository:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS workflow_traces (
                        trace_id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        intent TEXT NOT NULL,
                        steps TEXT NOT NULL,
                        requires_approval BOOLEAN NOT NULL
                    )
                    """
                )
                connection.commit()

    def reset(self) -> None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE workflow_traces")
                connection.commit()

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
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO workflow_traces (trace_id, conversation_id, intent, steps, requires_approval)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (trace.trace_id, trace.conversation_id, trace.intent, "\n".join(trace.steps), trace.requires_approval),
                )
                connection.commit()
        return trace

    def get(self, trace_id: str) -> WorkflowTrace | None:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT conversation_id, intent, steps, requires_approval
                    FROM workflow_traces
                    WHERE trace_id = %s
                    """,
                    (trace_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                conversation_id, intent, steps, requires_approval = row
                return WorkflowTrace(
                    trace_id=trace_id,
                    conversation_id=conversation_id,
                    intent=intent,
                    steps=steps.splitlines() if steps else [],
                    requires_approval=requires_approval,
                )

    def count(self) -> int:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM workflow_traces")
                return cursor.fetchone()[0]

    def list_recent(self, limit: int = 5) -> list[WorkflowTrace]:
        with closing(self._connect()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT trace_id, conversation_id, intent, steps, requires_approval
                    FROM workflow_traces
                    ORDER BY trace_id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
                return [
                    WorkflowTrace(
                        trace_id=trace_id,
                        conversation_id=conversation_id,
                        intent=intent,
                        steps=steps.splitlines() if steps else [],
                        requires_approval=requires_approval,
                    )
                    for trace_id, conversation_id, intent, steps, requires_approval in rows
                ]

    def _connect(self):
        from psycopg import connect

        return connect(self.dsn)
