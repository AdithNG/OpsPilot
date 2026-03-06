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

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) for the demo UI.

## Frontend

A real Next.js + TypeScript frontend now lives in `frontend/` and talks to the focused GraphQL API.

```bash
cd frontend
npm install
npm run dev
```

By default it calls `http://127.0.0.1:8010/api/graphql`. Override that with:

```bash
NEXT_PUBLIC_GRAPHQL_URL=http://127.0.0.1:8000/api/graphql
```

If API key protection is enabled on the backend, also set:

```bash
NEXT_PUBLIC_API_KEY=your-key
```

## Run with Docker

```bash
docker compose up --build
```

This starts:

- FastAPI demo and API on `http://127.0.0.1:8010/`
- PostgreSQL with pgvector inside the compose network

The compose stack sets `STORAGE_BACKEND=postgres`, so the app uses the database-backed repositories instead of the in-memory defaults.

## Test

```bash
pytest
```
