"use client";

import type { CSSProperties, FormEvent } from "react";
import { useEffect, useState } from "react";

import {
  CHAT_MUTATION,
  DASHBOARD_QUERY,
  type ChatMutationData,
  type DashboardData,
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
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSubmitting(true);
      setError(null);
      const data = await graphqlRequest<ChatMutationData>(CHAT_MUTATION, {
        message,
        conversationId,
      });
      setChatResult(data.chat);
      setConversationId(data.chat.conversationId);
      await loadDashboard();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to run chat mutation.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main style={styles.shell}>
      <section style={styles.heroCard}>
        <div>
          <p style={styles.kicker}>OpsPilot / GraphQL Console</p>
          <h1 style={styles.headline}>Operate the product, not just the API.</h1>
          <p style={styles.lead}>
            This frontend sits on top of the focused GraphQL endpoint and exposes the backend features as a real
            full-stack console: chat, traces, approvals, jobs, tools, and evals.
          </p>
        </div>
        <div style={styles.heroMeta}>
          <MetricCard
            label="GraphQL"
            value={getGraphqlUrl().replace(/^https?:\/\//, "")}
            tone="accent"
          />
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
        </div>
      </section>

      <section style={styles.grid}>
        <article style={styles.panelLarge}>
          <header style={styles.panelHeader}>
            <div>
              <p style={styles.eyebrow}>Live Chat</p>
              <h2 style={styles.panelTitle}>GraphQL mutation console</h2>
            </div>
            <button type="button" onClick={() => void loadDashboard()} style={styles.secondaryButton}>
              Refresh dashboard
            </button>
          </header>
          <form onSubmit={handleSubmit} style={styles.form}>
            <div style={styles.promptRow}>
              {starterPrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => setMessage(prompt)}
                  style={styles.promptChip}
                >
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
              <button type="submit" style={styles.primaryButton} disabled={submitting}>
                {submitting ? "Running..." : "Send mutation"}
              </button>
            </div>
          </form>
          {error ? <p style={styles.errorText}>{error}</p> : null}
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

        <article style={styles.panel}>
          <p style={styles.eyebrow}>Chat Result</p>
          <h2 style={styles.panelTitle}>Latest response</h2>
          {chatResult ? (
            <div style={styles.stack}>
              <p style={styles.responseText}>{chatResult.message}</p>
              <ul style={styles.list}>
                <li>Intent: {chatResult.intent}</li>
                <li>Approval required: {chatResult.requiresApproval ? "yes" : "no"}</li>
                <li>Trace steps: {chatResult.trace?.steps.join(" -> ") ?? "none"}</li>
              </ul>
              <div style={styles.stack}>
                <strong style={styles.subheading}>Citations</strong>
                {chatResult.citations.length ? (
                  chatResult.citations.map((citation) => (
                    <div key={`${citation.sourceId}-${citation.title ?? "source"}`} style={styles.inlineCard}>
                      <div style={styles.inlineLabel}>{citation.title ?? citation.sourceId}</div>
                      <div style={styles.inlineText}>{citation.snippet}</div>
                    </div>
                  ))
                ) : (
                  <p style={styles.muted}>No citations returned.</p>
                )}
              </div>
            </div>
          ) : (
            <p style={styles.muted}>Run a chat mutation to see a grounded response here.</p>
          )}
        </article>

        <article style={styles.panel}>
          <p style={styles.eyebrow}>Recent Jobs</p>
          <h2 style={styles.panelTitle}>Ingestion activity</h2>
          {dashboard?.ingestionJobs.length ? (
            <div style={styles.stack}>
              {dashboard.ingestionJobs.map((job) => (
                <div key={job.jobId} style={styles.inlineCard}>
                  <div style={styles.inlineLabel}>{job.jobType}</div>
                  <div style={styles.inlineText}>
                    {job.status} / {job.sourceKind} / chunks {job.chunksCreated}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={styles.muted}>No ingestion jobs yet.</p>
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
                </div>
              ))}
            </div>
          ) : (
            <p style={styles.muted}>No tool executions yet.</p>
          )}
        </article>

        <article style={styles.panel}>
          <p style={styles.eyebrow}>Approvals</p>
          <h2 style={styles.panelTitle}>Pending review items</h2>
          {dashboard?.approvals.length ? (
            <div style={styles.stack}>
              {dashboard.approvals.map((approval) => (
                <div key={approval.requestId} style={styles.inlineCard}>
                  <div style={styles.inlineLabel}>
                    {approval.status} <span style={styles.badge}>{approval.requestId}</span>
                  </div>
                  <div style={styles.inlineText}>{approval.action}</div>
                </div>
              ))}
            </div>
          ) : (
            <p style={styles.muted}>No approvals recorded.</p>
          )}
        </article>

        <article style={styles.panelWide}>
          <p style={styles.eyebrow}>Recent Traces</p>
          <h2 style={styles.panelTitle}>Workflow pathing</h2>
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

const styles: Record<string, CSSProperties> = {
  shell: {
    maxWidth: 1360,
    margin: "0 auto",
    padding: "36px 22px 80px",
  },
  heroCard: {
    display: "grid",
    gridTemplateColumns: "2fr 1.05fr",
    gap: 24,
    padding: 28,
    marginBottom: 24,
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
    margin: 0,
    maxWidth: 820,
    color: "var(--muted)",
    fontSize: 21,
    lineHeight: 1.45,
  },
  heroMeta: {
    display: "grid",
    gap: 14,
    alignContent: "start",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(12, 1fr)",
    gap: 20,
  },
  panelLarge: {
    gridColumn: "span 7",
    padding: 24,
    borderRadius: 26,
    background: "var(--surface)",
    border: "1px solid var(--border)",
    boxShadow: "var(--shadow)",
  },
  panelWide: {
    gridColumn: "span 8",
    padding: 24,
    borderRadius: 26,
    background: "var(--surface)",
    border: "1px solid var(--border)",
    boxShadow: "var(--shadow)",
  },
  panel: {
    gridColumn: "span 5",
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
  errorText: {
    color: "#a53d2c",
    marginTop: 14,
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
    gap: 6,
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
  },
  inlineText: {
    color: "var(--muted)",
    lineHeight: 1.4,
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
