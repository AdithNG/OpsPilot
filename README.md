# OpsPilot

OpsPilot is a production-style AI copilot for engineering and operations workflows.

## Current scope

- FastAPI backend scaffold
- Health, chat, document ingest, and approval endpoints
- Retrieval and workflow service stubs
- Pytest coverage for the initial API surface
- Docker and docker-compose for local development

## Run locally

```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

## Test

```bash
pytest
```
