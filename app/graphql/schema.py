from __future__ import annotations

import strawberry
from fastapi import Depends
from pydantic import HttpUrl
from strawberry.fastapi import GraphQLRouter

from app.core.config import settings
from app.core.security import enforce_api_protection
from app.core.storage import storage
from app.schemas.approvals import ApprovalDecisionRequest
from app.schemas.chat import ChatRequest
from app.schemas.documents import DocumentIngestRequest, GitHubIngestRequest
from app.schemas.observability import ObservabilitySummary
from app.services.approvals import ApprovalService
from app.services.evals import EvaluationService
from app.services.github_ingestion import GitHubIngestionService
from app.services.ingestion import IngestionService
from app.services.jobs import IngestionJobService
from app.services.tools import ToolService
from app.services.workflow import WorkflowService


@strawberry.type
class CitationType:
    source_id: str
    title: str | None
    source_url: str | None
    snippet: str
    score: float | None


@strawberry.type
class ApprovalRequestType:
    request_id: str
    action: str
    reason: str


@strawberry.type
class ConversationMessageType:
    role: str
    content: str


@strawberry.type
class WorkflowTraceType:
    trace_id: str
    conversation_id: str
    intent: str
    steps: list[str]
    requires_approval: bool


@strawberry.type
class IncidentActionItemType:
    owner: str
    action: str
    priority: str


@strawberry.type
class IncidentSummaryType:
    title: str
    impact: str
    severity: str
    suspected_cause: str
    next_steps: list[IncidentActionItemType]


@strawberry.type
class TicketDraftType:
    title: str
    summary: str
    impact: str
    reproduction_steps: list[str]
    acceptance_criteria: list[str]


@strawberry.type
class ToolExecutionType:
    execution_id: str
    conversation_id: str
    tool_name: str
    status: str
    input_text: str
    output_text: str
    metadata: strawberry.scalars.JSON


@strawberry.type
class ChatResponseType:
    conversation_id: str
    message: str
    intent: str
    citations: list[CitationType]
    requires_approval: bool
    approval: ApprovalRequestType | None
    incident_summary: IncidentSummaryType | None
    ticket_draft: TicketDraftType | None
    trace: WorkflowTraceType | None
    tool_executions: list[ToolExecutionType]


@strawberry.type
class ApprovalRecordType:
    request_id: str
    action: str
    status: str
    reviewer: str | None
    note: str | None


@strawberry.type
class IngestionJobType:
    job_id: str
    job_type: str
    status: str
    source_kind: str
    document_id: str | None
    chunks_created: int
    error_message: str | None


@strawberry.type
class ObservabilitySummaryType:
    storage_backend: str
    document_count: int
    conversation_count: int
    trace_count: int
    approval_count: int
    recent_traces: list[WorkflowTraceType]


@strawberry.type
class TraceEvaluationType:
    trace_id: str
    intent: str
    score: float
    passed: bool
    checks: list[str]


@strawberry.type
class EvaluationSummaryType:
    total_traces: int
    passed_traces: int
    average_score: float
    evaluations: list[TraceEvaluationType]


@strawberry.input
class ApprovalDecisionInput:
    approved: bool
    reviewer: str
    note: str | None = None


@strawberry.input
class DocumentIngestInput:
    title: str
    content: str
    source_url: str | None = None


@strawberry.input
class GitHubIngestInput:
    owner: str
    repo: str
    artifact_type: str
    ref: str = "main"
    path: str | None = None
    commit_sha: str | None = None
    pull_request_number: int | None = None


@strawberry.input
class ToolExecutionInput:
    conversation_id: str | None = None
    tool_name: str
    input_text: str


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> str:
        return "ok"

    @strawberry.field
    def observability_summary(self) -> ObservabilitySummaryType:
        summary = ObservabilitySummary(
            storage_backend=storage.backend,
            document_count=storage.documents.count(),
            conversation_count=storage.conversations.count(),
            trace_count=storage.traces.count(),
            approval_count=storage.approvals.count(),
            recent_traces=storage.traces.list_recent(limit=5),
        )
        return to_observability_summary(summary)

    @strawberry.field
    def approvals(self) -> list[ApprovalRecordType]:
        return [to_approval_record(record) for record in storage.approvals.list()]

    @strawberry.field
    def approval(self, request_id: str) -> ApprovalRecordType | None:
        record = storage.approvals.get(request_id)
        return to_approval_record(record) if record else None

    @strawberry.field
    def conversation(self, conversation_id: str) -> list[ConversationMessageType]:
        return [ConversationMessageType(role=item.role, content=item.content) for item in storage.conversations.get_messages(conversation_id)]

    @strawberry.field
    def trace(self, trace_id: str) -> WorkflowTraceType | None:
        trace = storage.traces.get(trace_id)
        return to_workflow_trace(trace) if trace else None

    @strawberry.field
    def ingestion_jobs(self, limit: int = 20) -> list[IngestionJobType]:
        return [to_ingestion_job(job) for job in storage.ingestion_jobs.list(limit=limit)]

    @strawberry.field
    def tool_executions(self, limit: int = 20) -> list[ToolExecutionType]:
        return [to_tool_execution(execution) for execution in storage.tools.list(limit=limit)]

    @strawberry.field
    def evaluation_summary(self, limit: int = 10) -> EvaluationSummaryType:
        return to_evaluation_summary(EvaluationService().summarize_recent(limit=limit))


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def chat(self, message: str, conversation_id: str | None = None) -> ChatResponseType:
        result = await WorkflowService().handle_chat(ChatRequest(message=message, conversation_id=conversation_id))
        return to_chat_response(result)

    @strawberry.mutation
    async def submit_approval_decision(self, request_id: str, decision: ApprovalDecisionInput) -> ApprovalRecordType:
        result = await ApprovalService().decide(
            request_id=request_id,
            decision=ApprovalDecisionRequest(
                approved=decision.approved,
                reviewer=decision.reviewer,
                note=decision.note,
            ),
        )
        return to_approval_record(result)

    @strawberry.mutation
    async def ingest_document(self, input: DocumentIngestInput) -> IngestionJobType:
        service = IngestionService()
        jobs = IngestionJobService()
        document_id = service.reserve_document_id()
        job = jobs.create(job_type="document_ingest", source_kind="document", document_id=document_id)
        request = DocumentIngestRequest(
            title=input.title,
            content=input.content,
            source_url=HttpUrl(input.source_url) if input.source_url else None,
        )
        jobs.mark_running(job.job_id)
        try:
            result = await service.ingest(request, document_id=document_id)
        except Exception as exc:
            failed = jobs.mark_failed(job.job_id, str(exc))
            return to_ingestion_job(failed or job)
        completed = jobs.mark_completed(job.job_id, result.chunks_created)
        return to_ingestion_job(completed or job)

    @strawberry.mutation
    async def ingest_github_artifact(self, input: GitHubIngestInput) -> IngestionJobType:
        service = GitHubIngestionService()
        ingestion_service = IngestionService()
        jobs = IngestionJobService()
        document_id = ingestion_service.reserve_document_id()
        job = jobs.create(job_type="github_ingest", source_kind=input.artifact_type, document_id=document_id)
        jobs.mark_running(job.job_id)
        try:
            artifact = service.fetch_artifact(
                GitHubIngestRequest(
                    owner=input.owner,
                    repo=input.repo,
                    artifact_type=input.artifact_type,  # type: ignore[arg-type]
                    ref=input.ref,
                    path=input.path,
                    commit_sha=input.commit_sha,
                    pull_request_number=input.pull_request_number,
                )
            )
            result = await ingestion_service.ingest(
                DocumentIngestRequest(
                    title=artifact.title,
                    content=artifact.content,
                    source_url=HttpUrl(artifact.source_url),
                ),
                document_id=document_id,
            )
        except Exception as exc:
            failed = jobs.mark_failed(job.job_id, str(exc))
            return to_ingestion_job(failed or job)
        completed = jobs.mark_completed(job.job_id, result.chunks_created)
        return to_ingestion_job(completed or job)

    @strawberry.mutation
    def queue_tool_execution(self, input: ToolExecutionInput) -> ToolExecutionType:
        execution = ToolService().queue(
            conversation_id=input.conversation_id,
            tool_name=input.tool_name,
            input_text=input.input_text,
        )
        ToolService().run(execution.execution_id)
        final_execution = ToolService().get(execution.execution_id)
        return to_tool_execution(final_execution)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema, path="", dependencies=[Depends(enforce_api_protection)])


def to_citation(citation) -> CitationType:
    return CitationType(
        source_id=citation.source_id,
        title=citation.title,
        source_url=citation.source_url,
        snippet=citation.snippet,
        score=citation.score,
    )


def to_approval_request(approval) -> ApprovalRequestType:
    return ApprovalRequestType(
        request_id=approval.request_id,
        action=approval.action,
        reason=approval.reason,
    )


def to_workflow_trace(trace) -> WorkflowTraceType:
    return WorkflowTraceType(
        trace_id=trace.trace_id,
        conversation_id=trace.conversation_id,
        intent=trace.intent,
        steps=list(trace.steps),
        requires_approval=trace.requires_approval,
    )


def to_incident_summary(summary) -> IncidentSummaryType:
    return IncidentSummaryType(
        title=summary.title,
        impact=summary.impact,
        severity=summary.severity,
        suspected_cause=summary.suspected_cause,
        next_steps=[
            IncidentActionItemType(owner=item.owner, action=item.action, priority=item.priority)
            for item in summary.next_steps
        ],
    )


def to_ticket_draft(draft) -> TicketDraftType:
    return TicketDraftType(
        title=draft.title,
        summary=draft.summary,
        impact=draft.impact,
        reproduction_steps=list(draft.reproduction_steps),
        acceptance_criteria=list(draft.acceptance_criteria),
    )


def to_tool_execution(execution) -> ToolExecutionType:
    return ToolExecutionType(
        execution_id=execution.execution_id,
        conversation_id=execution.conversation_id,
        tool_name=execution.tool_name,
        status=execution.status,
        input_text=execution.input_text,
        output_text=execution.output_text,
        metadata=execution.metadata,
    )


def to_chat_response(response) -> ChatResponseType:
    return ChatResponseType(
        conversation_id=response.conversation_id,
        message=response.message,
        intent=response.intent,
        citations=[to_citation(item) for item in response.citations],
        requires_approval=response.requires_approval,
        approval=to_approval_request(response.approval) if response.approval else None,
        incident_summary=to_incident_summary(response.incident_summary) if response.incident_summary else None,
        ticket_draft=to_ticket_draft(response.ticket_draft) if response.ticket_draft else None,
        trace=to_workflow_trace(response.trace) if response.trace else None,
        tool_executions=[to_tool_execution(item) for item in response.tool_executions],
    )


def to_approval_record(record) -> ApprovalRecordType:
    return ApprovalRecordType(
        request_id=record.request_id,
        action=record.action,
        status=record.status,
        reviewer=record.reviewer,
        note=record.note,
    )


def to_ingestion_job(job) -> IngestionJobType:
    return IngestionJobType(
        job_id=job.job_id,
        job_type=job.job_type,
        status=job.status,
        source_kind=job.source_kind,
        document_id=job.document_id,
        chunks_created=job.chunks_created,
        error_message=job.error_message,
    )


def to_observability_summary(summary) -> ObservabilitySummaryType:
    return ObservabilitySummaryType(
        storage_backend=summary.storage_backend,
        document_count=summary.document_count,
        conversation_count=summary.conversation_count,
        trace_count=summary.trace_count,
        approval_count=summary.approval_count,
        recent_traces=[to_workflow_trace(trace) for trace in summary.recent_traces],
    )


def to_trace_evaluation(evaluation) -> TraceEvaluationType:
    return TraceEvaluationType(
        trace_id=evaluation.trace_id,
        intent=evaluation.intent,
        score=evaluation.score,
        passed=evaluation.passed,
        checks=list(evaluation.checks),
    )


def to_evaluation_summary(summary) -> EvaluationSummaryType:
    return EvaluationSummaryType(
        total_traces=summary.total_traces,
        passed_traces=summary.passed_traces,
        average_score=summary.average_score,
        evaluations=[to_trace_evaluation(item) for item in summary.evaluations],
    )
