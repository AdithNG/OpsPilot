# OpsPilot Project Summary

## What OpsPilot is

OpsPilot is a production-style AI copilot for engineering and operations workflows.

The project is designed to look more like a real internal AI system than a toy chatbot. It combines retrieval, workflow orchestration, approval-gated actions, observability, evaluations, background jobs, and a full-stack operator console.

At a high level, OpsPilot can:

- answer questions over runbooks and internal engineering documents
- summarize incidents, outage notes, and operational context
- draft structured bug tickets and follow-up actions
- ingest documents and GitHub artifacts into a retrieval pipeline
- route requests through a LangGraph workflow
- pause for human approval before sensitive or write-like actions
- expose traces, jobs, tool runs, and evaluation results in a frontend console

## Why I built it

The goal of the project was to build something that matches what modern software engineer and AI engineer roles ask for in practice:

- Python backend development
- FastAPI APIs
- LangChain and LangGraph
- RAG and vector retrieval
- PostgreSQL and pgvector
- Dockerized local deployment
- GraphQL for frontend data composition
- Next.js and TypeScript for a real frontend
- background jobs, observability, tests, and production-style structure

Instead of building another chatbot demo, the project was shaped into an internal engineering ops copilot.

## Core product idea

A user can ask something like:

- "What does the deployment runbook say about rollback?"
- "Summarize this incident from the outage notes."
- "Draft a bug ticket for login failures after deploy."
- "Create a Jira ticket for this production issue."

OpsPilot then:

1. classifies the request
2. retrieves relevant context
3. routes the request through a LangGraph workflow
4. generates a grounded answer or structured artifact
5. records traces and tool executions
6. asks for approval if the request could change external state

## Main technologies used

### Backend

- Python
- FastAPI
- LangChain
- LangGraph
- PostgreSQL
- pgvector
- GraphQL
- Docker

### Frontend

- Next.js
- TypeScript
- CSS-based SPA shell

### Testing and local development

- pytest
- docker compose

## Architecture overview

OpsPilot is built in layers.

### 1. API layer

FastAPI provides the main backend API surface for:

- health checks
- chat requests
- document ingestion
- approval decisions
- conversations and traces
- observability summaries
- evaluations
- tool execution records

### 2. Workflow layer

LangGraph is used in `app/services/workflow.py` to route each request through a state graph.

The workflow includes nodes for:

- classify
- retrieve
- respond_question
- summarize_incident
- draft_ticket
- gate_action

This makes the project a workflow-driven AI system rather than a single prompt call.

### 3. Retrieval layer

OpsPilot uses a retrieval pipeline instead of relying only on model memory.

The retrieval flow is:

1. ingest documents or GitHub artifacts
2. split content into chunks
3. generate embeddings for chunks
4. store chunks and embeddings
5. embed the user query
6. retrieve candidate matches
7. rerank them before generation

The project supports:

- lexical search
- vector search
- reranking
- source-aware scoring

This was improved further after a real bug where a generic GitHub README outranked an actual rollback runbook for an ops question.

### 4. Generation layer

LangChain is used for:

- embeddings interface
- prompt/model abstraction
- structured parsing

The generation layer can return:

- grounded question answers
- structured incident summaries
- structured ticket drafts

### 5. Persistence layer

The app supports both:

- in-memory repositories
- PostgreSQL-backed repositories

Postgres stores:

- document chunks
- embeddings
- approvals
- conversations
- workflow traces
- tool executions
- ingestion jobs

When Docker Compose is used, the app runs against Postgres with pgvector enabled.

### 6. Frontend layer

The frontend is a Next.js + TypeScript SPA that talks to the backend through a focused GraphQL endpoint.

The SPA exposes:

- overview
- copilot
- sources
- approvals
- activity

This lets the frontend show the actual backend system behavior instead of just a single chat box.

## Major backend features implemented

### API and service foundation

- FastAPI app scaffold
- versioned API routes
- health endpoint
- structured schemas with Pydantic

### RAG and ingestion

- manual document ingestion
- GitHub artifact ingestion
- chunking and embedding
- Postgres + pgvector retrieval path
- reranking and source-aware retrieval improvements

### LangGraph workflow

- request classification
- retrieval step
- routed response generation
- structured incident/ticket outputs
- approval-gated action handling

### Persistence and observability

- persistent conversations
- persistent workflow traces
- read endpoints for conversations and traces
- observability summary endpoint
- evaluation scoring over traces

### Jobs and tools

- ingestion jobs
- async-style job tracking
- tool execution records
- queued, running, completed, blocked, failed states

### Production-style concerns

- optional API key auth
- rate limiting
- CORS handling for frontend/backend integration
- Docker and Compose support
- test coverage across the backend

## Major frontend features implemented

### Demo surface to full SPA

The frontend started as a thin demo page and was later turned into a more coherent operator console.

### GraphQL-powered SPA

The frontend now uses a focused GraphQL layer to:

- fetch dashboard data
- trigger chat mutations
- ingest documents and GitHub artifacts
- submit approval decisions

### Product-like operator views

The SPA includes views for:

- overview
- copilot interactions
- source ingestion
- approval handling
- activity, traces, jobs, and tool runs

### UX and polish work

- clearer sidebar navigation
- better interaction affordances
- approval UI
- source ingestion UI
- surfaced citations and structured outputs
- bug fixes for hydration mismatch confusion and duplicate citation keys

## What I learned from the project

### 1. AI engineering is not just prompt engineering

The hardest parts were not "calling an LLM." They were:

- retrieval quality
- workflow design
- observability
- evaluation
- failure handling
- human approval boundaries

### 2. RAG is a system, not a single library

The project uses libraries like LangChain, LangGraph, and pgvector, but the actual RAG pipeline is assembled inside the app:

- ingestion
- chunking
- embeddings
- storage
- retrieval
- reranking
- generation

### 3. Real AI products need guardrails

It is easy to demo a tool-calling chatbot.

It is harder, and more realistic, to build a system that:

- records what happened
- shows traces
- evaluates outputs
- asks for approval before risky actions

### 4. Frontend matters

The backend became much more believable once the project had a real frontend that exposed:

- sources
- approvals
- jobs
- traces
- evals

Instead of only returning JSON from endpoints.

## What the project demonstrates

OpsPilot demonstrates:

- full-stack engineering
- backend API design
- AI application architecture
- LangChain usage
- LangGraph workflow orchestration
- RAG implementation
- PostgreSQL and pgvector usage
- GraphQL integration
- frontend/backend coordination
- testing and local deployment

## Current state

OpsPilot is currently a strong portfolio-grade full-stack AI systems project.

It is credible for:

- software engineering interviews
- AI engineer interviews
- discussions around RAG, workflows, observability, approvals, and production tradeoffs

It is not yet a fully commercialized SaaS product, but it now covers a large part of the modern applied AI engineering stack.
