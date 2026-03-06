# OpsPilot

Repo: https://github.com/AdithNG/OpsPilot.git

## Premise

OpsPilot is a production-style AI copilot for engineering and operations workflows.

The goal of this project is to build an AI system that can:

- answer questions over engineering documents and runbooks
- summarize incidents, logs, and notes
- draft structured bug tickets or follow-up actions
- retrieve relevant context before responding
- use tools when needed
- require approval before sensitive or write-like actions

This project should be built like a real backend product, not a toy chatbot.

## Main idea

A user sends a request such as:

- "Summarize this incident"
- "What does the deployment runbook say about rollback?"
- "Draft a bug ticket from these notes"

OpsPilot should:

1. understand the request
2. retrieve relevant context if needed
3. decide whether a tool should be used
4. generate a grounded response
5. return structured output with citations when possible
6. flag any sensitive action for approval instead of executing it directly

## Tech direction

The project should be implemented as a Python backend using:

- FastAPI
- LangChain
- LangGraph
- PostgreSQL
- pgvector
- Docker

## Initial scope

Version 1 should focus on:

- backend API
- document ingestion
- retrieval over docs
- incident summarization
- ticket drafting
- approval-gated actions
- tests and clean project structure

## Build priority

Start small and grow in stages:

1. scaffold the backend
2. add health endpoint
3. add chat endpoint
4. add retrieval
5. add workflow orchestration
6. add summarization and ticket drafting
7. add tests and Docker support

## Important note for the coding agent

Prefer clean, modular, production-style code.
Do not overbuild the first version.
Avoid unnecessary frameworks or features outside the core scope.
