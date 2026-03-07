"use client";

import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";

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

type ViewKey = "overview" | "chat" | "sources" | "approvals" | "activity";
type ChatState = ChatMutationData["chat"] | null;

const starterPrompts = [
  "What does the deployment runbook say about rollback?",
  "Summarize this incident from the outage notes.",
  "Draft a bug ticket for login failures after deploy.",
  "Create a Jira ticket for this production issue.",
];

const navItems: Array<{ key: ViewKey; label: string; description: string }> = [
  { key: "overview", label: "Overview", description: "Product status and AI stack fit" },
  { key: "chat", label: "Copilot", description: "LangGraph + LangChain workflows" },
  { key: "sources", label: "Sources", description: "Document and GitHub ingestion" },
  { key: "approvals", label: "Approvals", description: "Human review and action gates" },
  { key: "activity", label: "Activity", description: "Jobs, tools, traces, and evals" },
];

export default function HomePage() {
  const [activeView, setActiveView] = useState<ViewKey>("overview");
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

  const pendingApprovals = dashboard?.approvals.filter((approval) => approval.status === "pending") ?? [];
  const activeNav = navItems.find((item) => item.key === activeView) ?? navItems[0];

  const topMetrics = useMemo(
    () => [
      { label: "GraphQL", value: getGraphqlUrl().replace(/^https?:\/\//, "") },
      { label: "Storage", value: dashboard?.observabilitySummary.storageBackend ?? "loading" },
      {
        label: "Eval Avg",
        value: dashboard ? dashboard.evaluationSummary.averageScore.toFixed(3) : "0.000",
      },
      {
        label: "Approvals",
        value: dashboard ? String(dashboard.observabilitySummary.approvalCount) : "0",
      },
    ],
    [dashboard],
  );

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
      setActivityMessage("Copilot run completed.");
      setActiveView("chat");
      await loadDashboard();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to run copilot mutation.");
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
      setActivityMessage(`Document ingest created ${data.ingestDocument.jobId}.`);
      setActiveView("sources");
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
      const data = await graphqlRequest<IngestGithubMutationData>(INGEST_GITHUB_MUTATION, {
        input: {
          owner: githubForm.owner,
          repo: githubForm.repo,
          artifactType: githubForm.artifactType,
          ref: githubForm.ref || "main",
          path: githubForm.path || null,
          commitSha: githubForm.commitSha || null,
          pullRequestNumber: githubForm.pullRequestNumber ? Number(githubForm.pullRequestNumber) : null,
        },
      });
      setActivityMessage(
        `GitHub ${data.ingestGithubArtifact.sourceKind} ingest created ${data.ingestGithubArtifact.jobId}.`,
      );
      setActiveView("sources");
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
          note: approved ? "Approved from the SPA console." : "Rejected from the SPA console.",
        },
      });
      setActivityMessage(`${data.submitApprovalDecision.requestId} marked ${data.submitApprovalDecision.status}.`);
      setActiveView("approvals");
      await loadDashboard();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to submit approval decision.");
    } finally {
      setApprovalBusy(null);
    }
  }

  return (
    <main className="ops-shell">
      <div className="ops-shell__backdrop" />
      <div className="ops-app">
        <aside className="ops-sidebar">
          <div className="ops-brand">
            <div className="ops-brand__mark">OP</div>
            <div>
              <p className="ops-brand__eyebrow">OpsPilot</p>
              <h1 className="ops-brand__title">AI Ops Console</h1>
            </div>
          </div>

          <p className="ops-sidebar__copy">
            A polished SPA for demonstrating the real backend: LangGraph routing, LangChain retrieval and generation,
            GitHub ingestion, approval gates, jobs, traces, and evals.
          </p>

          <nav className="ops-nav" aria-label="Workspace views">
            {navItems.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setActiveView(item.key)}
                className={`ops-nav__item ${activeView === item.key ? "is-active" : ""}`}
                aria-pressed={activeView === item.key}
              >
                <span className="ops-nav__content">
                  <span className="ops-nav__labelrow">
                    <span className="ops-nav__label">{item.label}</span>
                    <span className="ops-nav__action">{activeView === item.key ? "Viewing" : "Open"}</span>
                  </span>
                  <span className="ops-nav__desc">{item.description}</span>
                </span>
                <span className="ops-nav__chevron" aria-hidden="true">
                  {activeView === item.key ? "•" : "→"}
                </span>
              </button>
            ))}
          </nav>

          <div className="ops-sidebar__stack">
            <div className="ops-sidecard">
              <div className="ops-sidecard__label">GraphQL</div>
              <div className="ops-sidecard__value">{getGraphqlUrl().replace(/^https?:\/\//, "")}</div>
            </div>
            <div className="ops-sidecard">
              <div className="ops-sidecard__label">Current focus</div>
              <div className="ops-sidecard__value">{activeNav.label}</div>
              <p className="ops-sidecard__hint">{activeNav.description}</p>
            </div>
          </div>
        </aside>

        <section className="ops-main">
          <header className="ops-topbar">
            <div>
              <p className="ops-section__eyebrow">Workspace</p>
              <h2 className="ops-topbar__title">{activeNav.label}</h2>
              <p className="ops-topbar__subtitle">{activeNav.description}</p>
            </div>
            <div className="ops-metrics">
              {topMetrics.map((metric) => (
                <div key={metric.label} className="ops-metric">
                  <div className="ops-metric__label">{metric.label}</div>
                  <div className="ops-metric__value">{metric.value}</div>
                </div>
              ))}
            </div>
          </header>

          {(error || activityMessage) && (
            <div className={`ops-banner ${error ? "is-error" : "is-success"}`}>{error ?? activityMessage}</div>
          )}

          {activeView === "overview" && (
            <div className="ops-stage">
              <section className="ops-card ops-card--hero">
                <p className="ops-section__eyebrow">Product story</p>
                <h3 className="ops-card__title">Every backend feature now has a place in the frontend.</h3>
                <p className="ops-card__body">
                  Instead of showing disconnected panels, this SPA organizes the experience into operator workflows:
                  ask the copilot, ingest sources, handle approvals, and inspect activity.
                </p>
                <div className="ops-chiprow">
                  <span className="ops-chip">LangGraph workflow routing</span>
                  <span className="ops-chip">LangChain retrieval + structured outputs</span>
                  <span className="ops-chip">GitHub artifact ingestion</span>
                  <span className="ops-chip">Approval-gated actions</span>
                </div>
              </section>

              <div className="ops-grid ops-grid--2">
                <section className="ops-card">
                  <p className="ops-section__eyebrow">What the copilot does</p>
                  <h3 className="ops-card__title">LLM workflow layer</h3>
                  <ul className="ops-list">
                    <li>Routes requests through LangGraph states and records traces.</li>
                    <li>Uses LangChain embeddings and prompt pipelines for grounded responses.</li>
                    <li>Returns citations, structured incident summaries, and ticket drafts.</li>
                  </ul>
                </section>
                <section className="ops-card">
                  <p className="ops-section__eyebrow">What the operator does</p>
                  <h3 className="ops-card__title">Human-in-the-loop controls</h3>
                  <ul className="ops-list">
                    <li>Ingest documents or GitHub artifacts directly from the UI.</li>
                    <li>Approve or reject write-like actions before execution.</li>
                    <li>Inspect jobs, tool runs, traces, and eval summaries in one workspace.</li>
                  </ul>
                </section>
              </div>
            </div>
          )}

          {activeView === "chat" && (
            <div className="ops-stage">
              <section className="ops-card">
                <div className="ops-card__header">
                  <div>
                    <p className="ops-section__eyebrow">Copilot</p>
                    <h3 className="ops-card__title">Run the LangGraph workflow</h3>
                  </div>
                  <button type="button" onClick={() => void loadDashboard()} className="ops-button ops-button--ghost">
                    Refresh state
                  </button>
                </div>
                <form onSubmit={handleChatSubmit} className="ops-form">
                  <div className="ops-chiprow">
                    {starterPrompts.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => setMessage(prompt)}
                        className="ops-chip ops-chip--button"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                  <textarea
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                    className="ops-textarea"
                    rows={7}
                  />
                  <div className="ops-form__footer">
                    <span className="ops-muted">
                      {conversationId ? `Conversation: ${conversationId}` : "No active conversation"}
                    </span>
                    <button type="submit" className="ops-button" disabled={submittingChat}>
                      {submittingChat ? "Running..." : "Send mutation"}
                    </button>
                  </div>
                </form>
              </section>

              <section className="ops-card">
                <p className="ops-section__eyebrow">Output</p>
                <h3 className="ops-card__title">Grounded result and structured artifacts</h3>
                {chatResult ? (
                  <div className="ops-stack">
                    <p className="ops-callout">{chatResult.message}</p>
                    <div className="ops-detailrow">
                      <span className="ops-detailpill">Intent: {chatResult.intent}</span>
                      <span className="ops-detailpill">
                        Approval: {chatResult.requiresApproval ? "required" : "not required"}
                      </span>
                      <span className="ops-detailpill">
                        Trace: {chatResult.trace?.steps.join(" -> ") ?? "not captured"}
                      </span>
                    </div>

                    {chatResult.incidentSummary && (
                      <div className="ops-subcard">
                        <div className="ops-subcard__title">
                          Incident summary <span className="ops-chip">{chatResult.incidentSummary.severity}</span>
                        </div>
                        <p className="ops-subcard__body">{chatResult.incidentSummary.impact}</p>
                        <p className="ops-subcard__body">
                          Suspected cause: {chatResult.incidentSummary.suspectedCause}
                        </p>
                        <p className="ops-subcard__body">
                          {chatResult.incidentSummary.nextSteps
                            .map((step) => `${step.owner}: ${step.action} (${step.priority})`)
                            .join(" | ")}
                        </p>
                      </div>
                    )}

                    {chatResult.ticketDraft && (
                      <div className="ops-subcard">
                        <div className="ops-subcard__title">Ticket draft: {chatResult.ticketDraft.title}</div>
                        <p className="ops-subcard__body">{chatResult.ticketDraft.summary}</p>
                        <p className="ops-subcard__body">Impact: {chatResult.ticketDraft.impact}</p>
                        <p className="ops-subcard__body">
                          Acceptance: {chatResult.ticketDraft.acceptanceCriteria.join(" | ")}
                        </p>
                      </div>
                    )}

                    <div className="ops-stack">
                      <div className="ops-subtitle">Citations</div>
                      {chatResult.citations.length ? (
                        chatResult.citations.map((citation, index) => (
                          <div
                            key={`${citation.sourceId}-${citation.title ?? "source"}-${index}`}
                            className="ops-subcard"
                          >
                            <div className="ops-subcard__title">
                              {citation.title ?? citation.sourceId}
                              {citation.score !== null ? (
                                <span className="ops-chip">score {citation.score.toFixed(2)}</span>
                              ) : null}
                            </div>
                            <p className="ops-subcard__body">{citation.snippet}</p>
                            {citation.sourceUrl ? (
                              <a href={citation.sourceUrl} target="_blank" rel="noreferrer" className="ops-link">
                                {citation.sourceUrl}
                              </a>
                            ) : null}
                          </div>
                        ))
                      ) : (
                        <p className="ops-muted">No citations returned.</p>
                      )}
                    </div>
                  </div>
                ) : (
                  <p className="ops-muted">
                    Run a copilot request to see citations, tool runs, traces, and structured outputs here.
                  </p>
                )}
              </section>
            </div>
          )}

          {activeView === "sources" && (
            <div className="ops-stage">
              <div className="ops-grid ops-grid--2">
                <section className="ops-card">
                  <p className="ops-section__eyebrow">Documents</p>
                  <h3 className="ops-card__title">Manual ingestion</h3>
                  <form onSubmit={handleDocumentIngest} className="ops-form">
                    <input
                      value={docForm.title}
                      onChange={(event) => setDocForm((current) => ({ ...current, title: event.target.value }))}
                      placeholder="Document title"
                      className="ops-input"
                    />
                    <textarea
                      value={docForm.content}
                      onChange={(event) => setDocForm((current) => ({ ...current, content: event.target.value }))}
                      rows={6}
                      className="ops-textarea ops-textarea--compact"
                    />
                    <input
                      value={docForm.sourceUrl}
                      onChange={(event) => setDocForm((current) => ({ ...current, sourceUrl: event.target.value }))}
                      placeholder="Source URL"
                      className="ops-input"
                    />
                    <button type="submit" className="ops-button" disabled={submittingIngest}>
                      {submittingIngest ? "Submitting..." : "Ingest document"}
                    </button>
                  </form>
                </section>

                <section className="ops-card">
                  <p className="ops-section__eyebrow">GitHub</p>
                  <h3 className="ops-card__title">Artifact ingestion</h3>
                  <form onSubmit={handleGithubIngest} className="ops-form">
                    <div className="ops-form__grid">
                      <input
                        value={githubForm.owner}
                        onChange={(event) => setGithubForm((current) => ({ ...current, owner: event.target.value }))}
                        placeholder="Owner"
                        className="ops-input"
                      />
                      <input
                        value={githubForm.repo}
                        onChange={(event) => setGithubForm((current) => ({ ...current, repo: event.target.value }))}
                        placeholder="Repo"
                        className="ops-input"
                      />
                    </div>
                    <div className="ops-form__grid">
                      <select
                        value={githubForm.artifactType}
                        onChange={(event) =>
                          setGithubForm((current) => ({ ...current, artifactType: event.target.value }))
                        }
                        className="ops-input"
                      >
                        <option value="file">file</option>
                        <option value="commit">commit</option>
                        <option value="pull_request">pull_request</option>
                      </select>
                      <input
                        value={githubForm.ref}
                        onChange={(event) => setGithubForm((current) => ({ ...current, ref: event.target.value }))}
                        placeholder="Ref"
                        className="ops-input"
                      />
                    </div>
                    <input
                      value={githubForm.path}
                      onChange={(event) => setGithubForm((current) => ({ ...current, path: event.target.value }))}
                      placeholder="Path for file artifacts"
                      className="ops-input"
                    />
                    <div className="ops-form__grid">
                      <input
                        value={githubForm.commitSha}
                        onChange={(event) =>
                          setGithubForm((current) => ({ ...current, commitSha: event.target.value }))
                        }
                        placeholder="Commit SHA"
                        className="ops-input"
                      />
                      <input
                        value={githubForm.pullRequestNumber}
                        onChange={(event) =>
                          setGithubForm((current) => ({ ...current, pullRequestNumber: event.target.value }))
                        }
                        placeholder="PR number"
                        className="ops-input"
                      />
                    </div>
                    <button type="submit" className="ops-button" disabled={submittingIngest}>
                      {submittingIngest ? "Submitting..." : "Ingest GitHub artifact"}
                    </button>
                  </form>
                </section>
              </div>

              <section className="ops-card">
                <p className="ops-section__eyebrow">Queue</p>
                <h3 className="ops-card__title">Latest ingestion jobs</h3>
                {dashboard?.ingestionJobs.length ? (
                  <div className="ops-listgrid">
                    {dashboard.ingestionJobs.map((job) => (
                      <div key={job.jobId} className="ops-subcard">
                        <div className="ops-subcard__title">
                          {job.jobType} <span className="ops-chip">{job.status}</span>
                        </div>
                        <p className="ops-subcard__body">
                          Source: {job.sourceKind} | chunks {job.chunksCreated}
                        </p>
                        <div className="ops-traceid">{job.jobId}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="ops-muted">No ingestion jobs yet. Use the forms above to load sources into retrieval.</p>
                )}
              </section>
            </div>
          )}

          {activeView === "approvals" && (
            <div className="ops-stage">
              <section className="ops-card">
                <p className="ops-section__eyebrow">Human review</p>
                <h3 className="ops-card__title">Approval-gated actions</h3>
                <div className="ops-form__footer">
                  <input
                    value={reviewer}
                    onChange={(event) => setReviewer(event.target.value)}
                    placeholder="Reviewer name"
                    className="ops-input"
                  />
                </div>
                {dashboard?.approvals.length ? (
                  <div className="ops-stack">
                    {dashboard.approvals.map((approval) => (
                      <div key={approval.requestId} className="ops-subcard">
                        <div className="ops-subcard__title">
                          {approval.action}
                          <span className="ops-chip">{approval.status}</span>
                        </div>
                        <div className="ops-traceid">{approval.requestId}</div>
                        {approval.status === "pending" ? (
                          <div className="ops-buttonrow">
                            <button
                              type="button"
                              className="ops-button"
                              disabled={approvalBusy === approval.requestId}
                              onClick={() => void handleApprovalDecision(approval.requestId, true)}
                            >
                              Approve
                            </button>
                            <button
                              type="button"
                              className="ops-button ops-button--ghost"
                              disabled={approvalBusy === approval.requestId}
                              onClick={() => void handleApprovalDecision(approval.requestId, false)}
                            >
                              Reject
                            </button>
                          </div>
                        ) : (
                          <p className="ops-subcard__body">
                            Reviewed by {approval.reviewer ?? "unknown"}
                            {approval.note ? ` | ${approval.note}` : ""}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="ops-muted">
                    No approvals are pending. Trigger a write-like request in Copilot to see the human approval flow.
                  </p>
                )}
              </section>

              <section className="ops-card">
                <p className="ops-section__eyebrow">Why this matters</p>
                <h3 className="ops-card__title">Safe action execution</h3>
                <ul className="ops-list">
                  <li>Write-like actions do not auto-run.</li>
                  <li>Approvals become first-class backend records.</li>
                  <li>The frontend makes the review loop visible instead of hiding it in logs.</li>
                </ul>
                <div className="ops-chiprow">
                  <span className="ops-chip">{pendingApprovals.length} pending</span>
                  <span className="ops-chip">human in the loop</span>
                  <span className="ops-chip">auditable state</span>
                </div>
              </section>
            </div>
          )}

          {activeView === "activity" && (
            <div className="ops-stage">
              <div className="ops-grid ops-grid--2">
                <section className="ops-card">
                  <p className="ops-section__eyebrow">Tool runs</p>
                  <h3 className="ops-card__title">Recent executions</h3>
                  {dashboard?.toolExecutions.length ? (
                    <div className="ops-stack">
                      {dashboard.toolExecutions.map((execution) => (
                        <div key={execution.executionId} className="ops-subcard">
                          <div className="ops-subcard__title">
                            {execution.toolName}
                            <span className="ops-chip">{execution.status}</span>
                          </div>
                          <p className="ops-subcard__body">{execution.outputText}</p>
                          <div className="ops-traceid">{execution.executionId}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="ops-muted">No tool runs recorded yet.</p>
                  )}
                </section>

                <section className="ops-card">
                  <p className="ops-section__eyebrow">Traces</p>
                  <h3 className="ops-card__title">LangGraph pathing</h3>
                  {dashboard?.observabilitySummary.recentTraces.length ? (
                    <div className="ops-listgrid">
                      {dashboard.observabilitySummary.recentTraces.map((trace) => (
                        <div key={trace.traceId} className="ops-subcard">
                          <div className="ops-subcard__title">
                            {trace.intent}
                            <span className="ops-chip">{trace.requiresApproval ? "approval" : "auto"}</span>
                          </div>
                          <p className="ops-subcard__body">{trace.steps.join(" -> ")}</p>
                          <div className="ops-traceid">{trace.traceId}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="ops-muted">No traces captured yet.</p>
                  )}
                </section>
              </div>

              <section className="ops-card">
                <p className="ops-section__eyebrow">Evaluations</p>
                <h3 className="ops-card__title">Backend quality summary</h3>
                <div className="ops-detailrow">
                  <span className="ops-detailpill">
                    Average score: {dashboard ? dashboard.evaluationSummary.averageScore.toFixed(3) : "0.000"}
                  </span>
                  <span className="ops-detailpill">
                    Passed traces:{" "}
                    {dashboard
                      ? `${dashboard.evaluationSummary.passedTraces}/${dashboard.evaluationSummary.totalTraces}`
                      : "0/0"}
                  </span>
                </div>
              </section>
            </div>
          )}
        </section>

        <aside className="ops-rail">
          <section className="ops-card ops-card--sticky">
            <p className="ops-section__eyebrow">Live status</p>
            <h3 className="ops-card__title">Operator rail</h3>
            <div className="ops-stack">
              <div className="ops-subcard">
                <div className="ops-subcard__title">System snapshot</div>
                {loadingDashboard || !dashboard ? (
                  <p className="ops-subcard__body">Loading current backend state.</p>
                ) : (
                  <div className="ops-miniGrid">
                    <div>
                      <div className="ops-miniLabel">Documents</div>
                      <div className="ops-miniValue">{dashboard.observabilitySummary.documentCount}</div>
                    </div>
                    <div>
                      <div className="ops-miniLabel">Conversations</div>
                      <div className="ops-miniValue">{dashboard.observabilitySummary.conversationCount}</div>
                    </div>
                    <div>
                      <div className="ops-miniLabel">Traces</div>
                      <div className="ops-miniValue">{dashboard.observabilitySummary.traceCount}</div>
                    </div>
                    <div>
                      <div className="ops-miniLabel">Approvals</div>
                      <div className="ops-miniValue">{dashboard.observabilitySummary.approvalCount}</div>
                    </div>
                  </div>
                )}
              </div>

              <div className="ops-subcard">
                <div className="ops-subcard__title">Pending approvals</div>
                {pendingApprovals.length ? (
                  pendingApprovals.map((approval) => (
                    <div key={approval.requestId} className="ops-railitem">
                      <div>{approval.action}</div>
                      <div className="ops-traceid">{approval.requestId}</div>
                    </div>
                  ))
                ) : (
                  <p className="ops-subcard__body">No pending reviews.</p>
                )}
              </div>

              <div className="ops-subcard">
                <div className="ops-subcard__title">Latest jobs</div>
                {dashboard?.ingestionJobs.length ? (
                  dashboard.ingestionJobs.map((job) => (
                    <div key={job.jobId} className="ops-railitem">
                      <div>
                        {job.jobType} <span className="ops-chip">{job.status}</span>
                      </div>
                      <div className="ops-traceid">{job.sourceKind}</div>
                    </div>
                  ))
                ) : (
                  <p className="ops-subcard__body">No jobs yet.</p>
                )}
              </div>
            </div>
          </section>
        </aside>
      </div>
    </main>
  );
}
