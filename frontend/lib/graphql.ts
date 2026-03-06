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
      snippet: string;
    }>;
    trace: {
      traceId: string;
      steps: string[];
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
        snippet
      }
      trace {
        traceId
        steps
      }
      toolExecutions {
        executionId
        toolName
        status
      }
    }
  }
`;
