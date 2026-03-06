const DEFAULT_GRAPHQL_URL = "http://127.0.0.1:8010/api/graphql";

export function getGraphqlUrl(): string {
  return process.env.NEXT_PUBLIC_GRAPHQL_URL ?? DEFAULT_GRAPHQL_URL;
}

type GraphqlResponse<T> = {
  data?: T;
  errors?: Array<{ message: string }>;
};

export async function graphqlRequest<T>(
  query: string,
  variables?: Record<string, unknown>,
): Promise<T> {
  const response = await fetch(getGraphqlUrl(), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(process.env.NEXT_PUBLIC_API_KEY ? { "x-api-key": process.env.NEXT_PUBLIC_API_KEY } : {}),
    },
    body: JSON.stringify({ query, variables }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`GraphQL request failed with status ${response.status}`);
  }

  const payload = (await response.json()) as GraphqlResponse<T>;
  if (payload.errors?.length) {
    throw new Error(payload.errors.map((error) => error.message).join("; "));
  }
  if (!payload.data) {
    throw new Error("GraphQL response was missing data.");
  }
  return payload.data;
}

export type DashboardData = {
  observabilitySummary: {
    storageBackend: string;
    documentCount: number;
    conversationCount: number;
    traceCount: number;
    approvalCount: number;
    recentTraces: Array<{
      traceId: string;
      intent: string;
      steps: string[];
      requiresApproval: boolean;
    }>;
  };
  approvals: Array<{
    requestId: string;
    action: string;
    status: string;
    reviewer: string | null;
    note: string | null;
  }>;
  ingestionJobs: Array<{
    jobId: string;
    jobType: string;
    status: string;
    sourceKind: string;
    chunksCreated: number;
  }>;
  toolExecutions: Array<{
    executionId: string;
    toolName: string;
    status: string;
    outputText: string;
  }>;
  evaluationSummary: {
    averageScore: number;
    passedTraces: number;
    totalTraces: number;
  };
};

export const DASHBOARD_QUERY = `
  query DashboardData {
    observabilitySummary {
      storageBackend
      documentCount
      conversationCount
      traceCount
      approvalCount
      recentTraces {
        traceId
        intent
        steps
        requiresApproval
      }
    }
    approvals {
      requestId
      action
      status
      reviewer
      note
    }
    ingestionJobs(limit: 5) {
      jobId
      jobType
      status
      sourceKind
      chunksCreated
    }
    toolExecutions(limit: 5) {
      executionId
      toolName
      status
      outputText
    }
    evaluationSummary {
      averageScore
      passedTraces
      totalTraces
    }
  }
`;

export type ChatMutationData = {
  chat: {
    conversationId: string;
    intent: string;
    message: string;
    requiresApproval: boolean;
    citations: Array<{
      sourceId: string;
      title: string | null;
      sourceUrl: string | null;
      snippet: string;
      score: number | null;
    }>;
    trace: {
      traceId: string;
      steps: string[];
    } | null;
    incidentSummary: {
      title: string;
      impact: string;
      severity: string;
      suspectedCause: string;
      nextSteps: Array<{
        owner: string;
        action: string;
        priority: string;
      }>;
    } | null;
    ticketDraft: {
      title: string;
      summary: string;
      impact: string;
      reproductionSteps: string[];
      acceptanceCriteria: string[];
    } | null;
    toolExecutions: Array<{
      executionId: string;
      toolName: string;
      status: string;
    }>;
  };
};

export const CHAT_MUTATION = `
  mutation Chat($message: String!, $conversationId: String) {
    chat(message: $message, conversationId: $conversationId) {
      conversationId
      intent
      message
      requiresApproval
      citations {
        sourceId
        title
        sourceUrl
        snippet
        score
      }
      trace {
        traceId
        steps
      }
      incidentSummary {
        title
        impact
        severity
        suspectedCause
        nextSteps {
          owner
          action
          priority
        }
      }
      ticketDraft {
        title
        summary
        impact
        reproductionSteps
        acceptanceCriteria
      }
      toolExecutions {
        executionId
        toolName
        status
      }
    }
  }
`;

export type IngestDocumentMutationData = {
  ingestDocument: {
    jobId: string;
    jobType: string;
    status: string;
    documentId: string | null;
    chunksCreated: number;
  };
};

export const INGEST_DOCUMENT_MUTATION = `
  mutation IngestDocument($input: DocumentIngestInput!) {
    ingestDocument(input: $input) {
      jobId
      jobType
      status
      documentId
      chunksCreated
    }
  }
`;

export type IngestGithubMutationData = {
  ingestGithubArtifact: {
    jobId: string;
    jobType: string;
    status: string;
    sourceKind: string;
    documentId: string | null;
  };
};

export const INGEST_GITHUB_MUTATION = `
  mutation IngestGithubArtifact($input: GitHubIngestInput!) {
    ingestGithubArtifact(input: $input) {
      jobId
      jobType
      status
      sourceKind
      documentId
    }
  }
`;

export type ApprovalDecisionMutationData = {
  submitApprovalDecision: {
    requestId: string;
    status: string;
    reviewer: string | null;
    note: string | null;
  };
};

export const APPROVAL_DECISION_MUTATION = `
  mutation SubmitApprovalDecision($requestId: String!, $decision: ApprovalDecisionInput!) {
    submitApprovalDecision(requestId: $requestId, decision: $decision) {
      requestId
      status
      reviewer
      note
    }
  }
`;
