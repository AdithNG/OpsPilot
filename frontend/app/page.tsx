"use client";

import type { CSSProperties, FormEvent } from "react";
import { useEffect, useState } from "react";

import {
  APPROVAL_DECISION_MUTATION,
  CHAT_MUTATION,
  DASHBOARD_QUERY,
  INGEST_DOCUMENT_MUTATION,
  INGEST_GITHUB_MUTATION,
  type ApprovalDecisionMutationData,
  type ChatMutationData,
  type DashboardData,
  type IngestDocumentMutationData,
  type IngestGithubMutationData,
  graphqlRequest,
  getGraphqlUrl,
} from "../lib/graphql";

type ChatState = ChatMutationData["chat"] | null;

const starterPrompts = [
  "What does the deployment runbook say about rollback?",
  "Summarize this incident from the outage notes.",
  "Draft a bug ticket for login failures after deploy.",
  "Create a Jira ticket for this production issue.",
];

export default function HomePage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [chatResult, setChatResult] = useState<ChatState>(null);
  const [message, setMessage] = useState(starterPrompts[0]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [docForm, setDocForm] = useState({
    title: "Rollback Guide",
    content:
      "Rollback checklist: pause rollout, restore last known good image, verify login and checkout health checks, and notify stakeholders.",
    sourceUrl: "https://internal.example.com/runbooks/rollback",
  });
  const [githubForm, setGithubForm] = useState({
    owner: "openai",
    repo: "openai-cookbook",
    artifactType: "file",
    ref: "main",
    path: "README.md",
    commitSha: "",
    pullRequestNumber: "",
  });
  const [reviewer, setReviewer] = useState("ops-reviewer");
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [submittingChat, setSubmittingChat] = useState(false);
  const [submittingIngest, setSubmittingIngest] = useState(false);
  const [approvalBusy, setApprovalBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activityMessage, setActivityMessage] = useState<string | null>(null);

  async function loadDashboard() {
    try {
      setLoadingDashboard(true);
      setError(null);
      const data = await graphqlRequest<DashboardData>(DASHBOARD_QUERY);
      setDashboard(data);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load dashboard.");
    } finally {
      setLoadingDashboard(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  async function handleChatSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSubmittingChat(true);
      setError(null);
      setActivityMessage(null);
      const data = await graphqlRequest<ChatMutationData>(CHAT_MUTATION, {
        message,
        conversationId,
      });
      setChatResult(data.chat);
      setConversationId(data.chat.conversationId);
      setActivityMessage("Chat mutation completed.");
      await loadDashboard();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to run chat mutation.");
    } finally {
      setSubmittingChat(false);
    }
  }

  async function handleDocumentIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSubmittingIngest(true);
      setError(null);
      setActivityMessage(null);
      const data = await graphqlRequest<IngestDocumentMutationData>(INGEST_DOCUMENT_MUTATION, {
        input: {
          title: docForm.title,
          content: docForm.content,
          sourceUrl: docForm.sourceUrl || null,
        },
      });
      setActivityMessage(`Document ingestion queued as ${data.ingestDocument.jobId}.`);
      await loadDashboard();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to ingest document.");
    } finally {
      setSubmittingIngest(false);
    }
  }

  async function handleGithubIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSubmittingIngest(true);
      setError(null);
      setActivityMessage(null);
      const variables = {
        input: {
          owner: githubForm.owner,
          repo: githubForm.repo,
          artifactType: githubForm.artifactType,
          ref: githubForm.ref || "main",
          path: githubForm.path || null,
          commitSha: githubForm.commitSha || null,
          pullRequestNumber: githubForm.pullRequestNumber ? Number(githubForm.pullRequestNumber) : null,
        },
      };
      const data = await graphqlRequest<IngestGithubMutationData>(INGEST_GITHUB_MUTATION, variables);
      setActivityMessage(
        `GitHub ${data.ingestGithubArtifact.sourceKind} ingestion queued as ${data.ingestGithubArtifact.jobId}.`,
      );
      await loadDashboard();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to ingest GitHub artifact.");
    } finally {
      setSubmittingIngest(false);
    }
  }

  async function handleApprovalDecision(requestId: string, approved: boolean) {
    try {
      setApprovalBusy(requestId);
      setError(null);
      setActivityMessage(null);
      const data = await graphqlRequest<ApprovalDecisionMutationData>(APPROVAL_DECISION_MUTATION, {
        requestId,
        decision: {
          approved,
          reviewer,
          note: approved ? "Approved from the showcase dashboard." : "Rejected from the showcase dashboard.",
        },
      });
      setActivityMessage(`${data.submitApprovalDecision.requestId} marked ${data.submitApprovalDecision.status}.`);
      await loadDashboard();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to submit approval decision.");
    } finally {
      setApprovalBusy(null);
    }
  }

  const pendingApprovals = dashboard?.approvals.filter((approval) => approval.status === "pending") ?? [];

  return (
    <main style={styles.shell}>
      <section style={styles.heroCard}>
        <div>
          <p style={styles.kicker}>OpsPilot / Full-Stack Showcase</p>
          <h1 style={styles.headline}>Every backend capability should be visible in the product.</h1>
          <p style={styles.lead}>
            This dashboard now exposes chat, citations, structured outputs, GitHub ingestion, document ingestion,
            approvals, job tracking, tool runs, traces, and evals over the GraphQL API.
          </p>
          <div style={styles.promptRow}>
            <Tag text="LangGraph workflow routing" />
            <Tag text="LangChain retrieval + generation" />
            <Tag text="GitHub artifact ingestion" />
            <Tag text="Approval-gated actions" />
          </div>
        </div>
        <div style={styles.heroMeta}>
          <MetricCard label="GraphQL" value={getGraphqlUrl().replace(/^https?:\/\//, "")} tone="accent" />
          <MetricCard
            label="Storage"
            value={dashboard?.observabilitySummary.storageBackend ?? "loading"}
            tone="warm"
          />
          <MetricCard
            label="Eval Avg"
            value={dashboard ? dashboard.evaluationSummary.averageScore.toFixed(3) : "0.000"}
            tone="neutral"
          />
          <MetricCard
            label="Passed Traces"
            value={
              dashboard
                ? `${dashboard.evaluationSummary.passedTraces}/${dashboard.evaluationSummary.totalTraces}`
                : "0/0"
            }
            tone="neutral"
          />
        </div>
      </section>

      {(error || activityMessage) && (
        <section style={{ ...styles.notice, color: error ? "#a53d2c" : "var(--accent-strong)" }}>
          {error ?? activityMessage}
        </section>
      )}

      <section style={styles.grid}>
        <article style={styles.panelLarge}>
          <header style={styles.panelHeader}>
            <div>
              <p style={styles.eyebrow}>Live Chat</p>
              <h2 style={styles.panelTitle}>LangGraph + LangChain console</h2>
            </div>
            <button type="button" onClick={() => void loadDashboard()} style={styles.secondaryButton}>
              Refresh dashboard
            </button>
          </header>
          <form onSubmit={handleChatSubmit} style={styles.form}>
            <div style={styles.promptRow}>
              {starterPrompts.map((prompt) => (
                <button key={prompt} type="button" onClick={() => setMessage(prompt)} style={styles.promptChip}>
                  {prompt}
                </button>
              ))}
            </div>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              style={styles.textarea}
              rows={6}
            />
            <div style={styles.formFooter}>
              <div style={styles.metaText}>
                {conversationId ? `Conversation: ${conversationId}` : "No conversation yet"}
              </div>
              <button type="submit" style={styles.primaryButton} disabled={submittingChat}>
                {submittingChat ? "Running..." : "Send mutation"}
              </button>
            </div>
          </form>
        </article>

        <article style={styles.panel}>
          <p style={styles.eyebrow}>Source Lab</p>
          <h2 style={styles.panelTitle}>Backend ingestion features</h2>
          <div style={styles.stack}>
            <form onSubmit={handleDocumentIngest} style={styles.formBlock}>
              <strong style={styles.subheading}>Manual document ingest</strong>
              <input
                value={docForm.title}
                onChange={(event) => setDocForm((current) => ({ ...current, title: event.target.value }))}
                placeholder="Document title"
                style={styles.input}
              />
              <textarea
                value={docForm.content}
                onChange={(event) => setDocForm((current) => ({ ...current, content: event.target.value }))}
                rows={4}
                style={styles.smallTextarea}
              />
              <input
                value={docForm.sourceUrl}
                onChange={(event) => setDocForm((current) => ({ ...current, sourceUrl: event.target.value }))}
                placeholder="Source URL"
                style={styles.input}
              />
              <button type="submit" style={styles.primaryButton} disabled={submittingIngest}>
                Ingest document
              </button>
            </form>

            <form onSubmit={handleGithubIngest} style={styles.formBlock}>
              <strong style={styles.subheading}>GitHub artifact ingest</strong>
              <div style={styles.twoUp}>
                <input
                  value={githubForm.owner}
                  onChange={(event) => setGithubForm((current) => ({ ...current, owner: event.target.value }))}
                  placeholder="Owner"
                  style={styles.input}
                />
                <input
                  value={githubForm.repo}
                  onChange={(event) => setGithubForm((current) => ({ ...current, repo: event.target.value }))}
                  placeholder="Repo"
                  style={styles.input}
                />
              </div>
              <div style={styles.twoUp}>
                <select
                  value={githubForm.artifactType}
                  onChange={(event) =>
                    setGithubForm((current) => ({ ...current, artifactType: event.target.value }))
                  }
                  style={styles.input}
                >
                  <option value="file">file</option>
                  <option value="commit">commit</option>
                  <option value="pull_request">pull_request</option>
                </select>
                <input
                  value={githubForm.ref}
                  onChange={(event) => setGithubForm((current) => ({ ...current, ref: event.target.value }))}
                  placeholder="Ref"
                  style={styles.input}
                />
              </div>
              <input
                value={githubForm.path}
                onChange={(event) => setGithubForm((current) => ({ ...current, path: event.target.value }))}
                placeholder="Path for file artifacts"
                style={styles.input}
              />
              <div style={styles.twoUp}>
                <input
                  value={githubForm.commitSha}
                  onChange={(event) => setGithubForm((current) => ({ ...current, commitSha: event.target.value }))}
                  placeholder="Commit SHA"
                  style={styles.input}
                />
                <input
                  value={githubForm.pullRequestNumber}
                  onChange={(event) =>
                    setGithubForm((current) => ({ ...current, pullRequestNumber: event.target.value }))
                  }
                  placeholder="PR number"
                  style={styles.input}
                />
              </div>
              <button type="submit" style={styles.primaryButton} disabled={submittingIngest}>
                Ingest GitHub artifact
              </button>
            </form>
          </div>
        </article>

        <article style={styles.panel}>
          <p style={styles.eyebrow}>Observability</p>
          <h2 style={styles.panelTitle}>System snapshot</h2>
          {loadingDashboard || !dashboard ? (
            <p style={styles.muted}>Loading current backend state.</p>
          ) : (
            <div style={styles.metricGrid}>
              <MetricCard label="Documents" value={String(dashboard.observabilitySummary.documentCount)} tone="neutral" />
              <MetricCard
                label="Conversations"
                value={String(dashboard.observabilitySummary.conversationCount)}
                tone="neutral"
              />
              <MetricCard label="Traces" value={String(dashboard.observabilitySummary.traceCount)} tone="neutral" />
              <MetricCard label="Approvals" value={String(dashboard.observabilitySummary.approvalCount)} tone="neutral" />
            </div>
          )}
        </article>

        <article style={styles.panelLarge}>
          <p style={styles.eyebrow}>Chat Result</p>
          <h2 style={styles.panelTitle}>Grounded output + structured artifacts</h2>
          {chatResult ? (
            <div style={styles.stack}>
              <p style={styles.responseText}>{chatResult.message}</p>
              <ul style={styles.list}>
                <li>Intent: {chatResult.intent}</li>
                <li>Approval required: {chatResult.requiresApproval ? "yes" : "no"}</li>
                <li>Trace steps: {chatResult.trace?.steps.join(" -> ") ?? "none"}</li>
              </ul>

              {chatResult.incidentSummary && (
                <div style={styles.inlineCard}>
                  <div style={styles.inlineLabel}>Incident summary · {chatResult.incidentSummary.severity}</div>
                  <div style={styles.inlineText}>{chatResult.incidentSummary.impact}</div>
                  <div style={styles.inlineText}>
                    Cause: {chatResult.incidentSummary.suspectedCause}
                  </div>
                  <div style={styles.inlineText}>
                    Next steps:{" "}
                    {chatResult.incidentSummary.nextSteps
                      .map((step) => `${step.owner}: ${step.action} (${step.priority})`)
                      .join(" | ")}
                  </div>
                </div>
              )}

              {chatResult.ticketDraft && (
                <div style={styles.inlineCard}>
                  <div style={styles.inlineLabel}>Ticket draft · {chatResult.ticketDraft.title}</div>
                  <div style={styles.inlineText}>{chatResult.ticketDraft.summary}</div>
                  <div style={styles.inlineText}>Impact: {chatResult.ticketDraft.impact}</div>
                  <div style={styles.inlineText}>
                    Acceptance: {chatResult.ticketDraft.acceptanceCriteria.join(" | ")}
                  </div>
                </div>
              )}

              <div style={styles.stack}>
                <strong style={styles.subheading}>Citations</strong>
                {chatResult.citations.length ? (
                  chatResult.citations.map((citation) => (
                    <div key={`${citation.sourceId}-${citation.title ?? "source"}`} style={styles.inlineCard}>
                      <div style={styles.inlineLabel}>
                        {citation.title ?? citation.sourceId}
                        {citation.score !== null ? (
                          <span style={styles.badge}>score {citation.score.toFixed(2)}</span>
                        ) : null}
                      </div>
                      <div style={styles.inlineText}>{citation.snippet}</div>
                      {citation.sourceUrl ? (
                        <a href={citation.sourceUrl} target="_blank" rel="noreferrer" style={styles.link}>
                          {citation.sourceUrl}
                        </a>
                      ) : null}
                    </div>
                  ))
                ) : (
                  <p style={styles.muted}>No citations returned.</p>
                )}
              </div>
            </div>
          ) : (
            <p style={styles.muted}>Run chat to see citations, structured output, tools, and workflow routing.</p>
          )}
        </article>

        <article style={styles.panel}>
          <p style={styles.eyebrow}>Recent Jobs</p>
          <h2 style={styles.panelTitle}>Ingestion activity</h2>
          {dashboard?.ingestionJobs.length ? (
            <div style={styles.stack}>
              {dashboard.ingestionJobs.map((job) => (
                <div key={job.jobId} style={styles.inlineCard}>
                  <div style={styles.inlineLabel}>
                    {job.jobType} <span style={styles.badge}>{job.status}</span>
                  </div>
                  <div style={styles.inlineText}>
                    Source: {job.sourceKind} · chunks {job.chunksCreated}
                  </div>
                  <div style={styles.traceId}>{job.jobId}</div>
                </div>
              ))}
            </div>
          ) : (
            <p style={styles.muted}>Use the Source Lab above to create document and GitHub ingestion jobs.</p>
          )}
        </article>

        <article style={styles.panel}>
          <p style={styles.eyebrow}>Tool Runs</p>
          <h2 style={styles.panelTitle}>Latest executions</h2>
          {dashboard?.toolExecutions.length ? (
            <div style={styles.stack}>
              {dashboard.toolExecutions.map((execution) => (
                <div key={execution.executionId} style={styles.inlineCard}>
                  <div style={styles.inlineLabel}>
                    {execution.toolName} <span style={styles.badge}>{execution.status}</span>
                  </div>
                  <div style={styles.inlineText}>{execution.outputText}</div>
                  <div style={styles.traceId}>{execution.executionId}</div>
                </div>
              ))}
            </div>
          ) : (
            <p style={styles.muted}>Tool executions appear after incident summaries, tickets, and queued actions.</p>
          )}
        </article>

        <article style={styles.panel}>
          <p style={styles.eyebrow}>Approvals</p>
          <h2 style={styles.panelTitle}>Approval-gated actions</h2>
          <div style={styles.stack}>
            <input
              value={reviewer}
              onChange={(event) => setReviewer(event.target.value)}
              placeholder="Reviewer name"
              style={styles.input}
            />
            {dashboard?.approvals.length ? (
              dashboard.approvals.map((approval) => (
                <div key={approval.requestId} style={styles.inlineCard}>
                  <div style={styles.inlineLabel}>
                    {approval.status} <span style={styles.badge}>{approval.requestId}</span>
                  </div>
                  <div style={styles.inlineText}>{approval.action}</div>
                  {approval.status === "pending" ? (
                    <div style={styles.buttonRow}>
                      <button
                        type="button"
                        style={styles.primaryButton}
                        disabled={approvalBusy === approval.requestId}
                        onClick={() => void handleApprovalDecision(approval.requestId, true)}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        style={styles.secondaryButton}
                        disabled={approvalBusy === approval.requestId}
                        onClick={() => void handleApprovalDecision(approval.requestId, false)}
                      >
                        Reject
                      </button>
                    </div>
                  ) : (
                    <div style={styles.inlineText}>
                      Reviewed by {approval.reviewer ?? "unknown"}{approval.note ? ` · ${approval.note}` : ""}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p style={styles.muted}>Ask the chat to create a Jira ticket to trigger the approval flow.</p>
            )}
          </div>
        </article>

        <article style={styles.panelWide}>
          <p style={styles.eyebrow}>Workflow pathing</p>
          <h2 style={styles.panelTitle}>LangGraph traces</h2>
          {dashboard?.observabilitySummary.recentTraces.length ? (
            <div style={styles.traceGrid}>
              {dashboard.observabilitySummary.recentTraces.map((trace) => (
                <div key={trace.traceId} style={styles.traceCard}>
                  <div style={styles.inlineLabel}>
                    {trace.intent} <span style={styles.badge}>{trace.requiresApproval ? "approval" : "auto"}</span>
                  </div>
                  <div style={styles.inlineText}>{trace.steps.join(" -> ")}</div>
                  <div style={styles.traceId}>{trace.traceId}</div>
                </div>
              ))}
            </div>
          ) : (
            <p style={styles.muted}>No traces yet.</p>
          )}
        </article>

        <article style={styles.panelWide}>
          <p style={styles.eyebrow}>AI Stack</p>
          <h2 style={styles.panelTitle}>What the backend is showing off</h2>
          <div style={styles.traceGrid}>
            <div style={styles.traceCard}>
              <div style={styles.inlineLabel}>LangGraph</div>
              <div style={styles.inlineText}>
                Request routing, step-by-step traces, approval gates, and multi-stage workflows.
              </div>
            </div>
            <div style={styles.traceCard}>
              <div style={styles.inlineLabel}>LangChain</div>
              <div style={styles.inlineText}>
                Embeddings, prompt-driven generation, structured outputs, and retrieval grounding with citations.
              </div>
            </div>
            <div style={styles.traceCard}>
              <div style={styles.inlineLabel}>GitHub + Docs</div>
              <div style={styles.inlineText}>
                Ingest public repo files, commits, pull requests, or manual documents into the same retrieval path.
              </div>
            </div>
          </div>
        </article>
      </section>
    </main>
  );
}

function MetricCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "accent" | "warm" | "neutral";
}) {
  const accent =
    tone === "accent"
      ? "rgba(14, 139, 127, 0.12)"
      : tone === "warm"
        ? "rgba(211, 130, 69, 0.14)"
        : "rgba(22, 32, 44, 0.04)";
  return (
    <div style={{ ...styles.metricCard, background: accent }}>
      <div style={styles.metricLabel}>{label}</div>
      <div style={styles.metricValue}>{value}</div>
    </div>
  );
}

function Tag({ text }: { text: string }) {
  return <span style={styles.badge}>{text}</span>;
}

const styles: Record<string, CSSProperties> = {
  shell: {
    maxWidth: 1440,
    margin: "0 auto",
    padding: "36px 22px 80px",
  },
  heroCard: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
    gap: 24,
    padding: 28,
    marginBottom: 20,
    borderRadius: 28,
    background: "var(--surface)",
    border: "1px solid var(--border)",
    boxShadow: "var(--shadow)",
    backdropFilter: "blur(18px)",
  },
  kicker: {
    margin: 0,
    letterSpacing: "0.24em",
    textTransform: "uppercase",
    color: "var(--accent)",
    fontSize: 12,
  },
  headline: {
    margin: "12px 0 10px",
    fontSize: "clamp(2.8rem, 5vw, 5.2rem)",
    lineHeight: 0.92,
  },
  lead: {
    margin: "0 0 18px",
    maxWidth: 860,
    color: "var(--muted)",
    fontSize: 21,
    lineHeight: 1.45,
  },
  heroMeta: {
    display: "grid",
    gap: 14,
    alignContent: "start",
  },
  notice: {
    padding: "14px 18px",
    marginBottom: 20,
    borderRadius: 18,
    background: "rgba(255,255,255,0.45)",
    border: "1px solid var(--border)",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
    gap: 20,
  },
  panelLarge: {
    gridColumn: "span 2",
    padding: 24,
    borderRadius: 26,
    background: "var(--surface)",
    border: "1px solid var(--border)",
    boxShadow: "var(--shadow)",
  },
  panelWide: {
    gridColumn: "span 2",
    padding: 24,
    borderRadius: 26,
    background: "var(--surface)",
    border: "1px solid var(--border)",
    boxShadow: "var(--shadow)",
  },
  panel: {
    padding: 24,
    borderRadius: 26,
    background: "var(--surface)",
    border: "1px solid var(--border)",
    boxShadow: "var(--shadow)",
  },
  panelHeader: {
    display: "flex",
    justifyContent: "space-between",
    gap: 16,
    alignItems: "start",
    marginBottom: 18,
  },
  eyebrow: {
    margin: 0,
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: "0.18em",
    color: "var(--muted)",
  },
  panelTitle: {
    margin: "8px 0 0",
    fontSize: 34,
    lineHeight: 1,
  },
  form: {
    display: "grid",
    gap: 18,
  },
  formBlock: {
    display: "grid",
    gap: 12,
    padding: 16,
    borderRadius: 18,
    border: "1px solid var(--border)",
    background: "rgba(255,255,255,0.42)",
  },
  promptRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: 10,
  },
  promptChip: {
    border: "1px solid var(--border)",
    background: "var(--surface-strong)",
    borderRadius: 999,
    padding: "10px 14px",
    cursor: "pointer",
  },
  textarea: {
    width: "100%",
    borderRadius: 22,
    minHeight: 180,
    padding: 20,
    border: "1px solid var(--border)",
    background: "rgba(255,255,255,0.45)",
    resize: "vertical",
  },
  smallTextarea: {
    width: "100%",
    borderRadius: 18,
    minHeight: 108,
    padding: 16,
    border: "1px solid var(--border)",
    background: "rgba(255,255,255,0.45)",
    resize: "vertical",
  },
  input: {
    width: "100%",
    borderRadius: 14,
    padding: "12px 14px",
    border: "1px solid var(--border)",
    background: "rgba(255,255,255,0.52)",
  },
  twoUp: {
    display: "grid",
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    gap: 10,
  },
  formFooter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 16,
  },
  metaText: {
    color: "var(--muted)",
    fontSize: 14,
  },
  buttonRow: {
    display: "flex",
    gap: 10,
    flexWrap: "wrap",
  },
  primaryButton: {
    border: "none",
    borderRadius: 999,
    background: "var(--accent)",
    color: "white",
    padding: "12px 18px",
    cursor: "pointer",
  },
  secondaryButton: {
    border: "1px solid var(--border)",
    borderRadius: 999,
    background: "var(--surface-strong)",
    padding: "11px 16px",
    cursor: "pointer",
  },
  muted: {
    color: "var(--muted)",
    margin: 0,
  },
  responseText: {
    margin: 0,
    fontSize: 18,
    lineHeight: 1.5,
  },
  stack: {
    display: "grid",
    gap: 14,
  },
  list: {
    margin: 0,
    paddingLeft: 18,
    color: "var(--muted)",
  },
  subheading: {
    fontSize: 14,
    textTransform: "uppercase",
    letterSpacing: "0.16em",
    color: "var(--muted)",
  },
  inlineCard: {
    display: "grid",
    gap: 8,
    padding: 14,
    borderRadius: 18,
    border: "1px solid var(--border)",
    background: "rgba(255,255,255,0.42)",
  },
  inlineLabel: {
    display: "flex",
    gap: 8,
    alignItems: "center",
    fontWeight: 700,
    flexWrap: "wrap",
  },
  inlineText: {
    color: "var(--muted)",
    lineHeight: 1.4,
  },
  link: {
    color: "var(--accent-strong)",
    textDecoration: "none",
    wordBreak: "break-all",
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    padding: "3px 8px",
    borderRadius: 999,
    background: "rgba(14, 139, 127, 0.12)",
    color: "var(--accent-strong)",
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: "0.08em",
  },
  traceGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: 14,
  },
  traceCard: {
    display: "grid",
    gap: 10,
    padding: 16,
    borderRadius: 18,
    border: "1px solid var(--border)",
    background: "rgba(255,255,255,0.46)",
  },
  traceId: {
    fontSize: 12,
    color: "var(--muted)",
    wordBreak: "break-all",
  },
  metricGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    gap: 14,
  },
  metricCard: {
    padding: 18,
    borderRadius: 18,
    border: "1px solid var(--border)",
  },
  metricLabel: {
    color: "var(--muted)",
    textTransform: "uppercase",
    letterSpacing: "0.14em",
    fontSize: 12,
    marginBottom: 8,
  },
  metricValue: {
    fontSize: 22,
    lineHeight: 1.2,
    wordBreak: "break-word",
  },
};
