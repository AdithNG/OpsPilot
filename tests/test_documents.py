from fastapi.testclient import TestClient

from app.main import app
from app.services.github_ingestion import GitHubArtifact

client = TestClient(app)


def test_document_ingest_returns_queued_job() -> None:
    response = client.post(
        "/api/v1/documents/ingest",
        json={
            "title": "Rollback Runbook",
            "content": "Rollback checklist " * 60,
            "source_url": "https://example.com/runbook",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "queued"
    assert payload["job_id"].startswith("job-")
    assert payload["chunks_created"] == 0

    job_response = client.get(f"/api/v1/documents/jobs/{payload['job_id']}")
    assert job_response.status_code == 200
    job_payload = job_response.json()
    assert job_payload["status"] == "completed"
    assert job_payload["chunks_created"] >= 1


def test_github_commit_ingest_returns_queued_job(monkeypatch) -> None:
    def fake_fetch_artifact(self, request):
        return GitHubArtifact(
            title="ops commit abc1234",
            content="Commit message: Fix login rollback handling and update health checks.",
            source_url="https://github.com/example/ops/commit/abc1234",
        )

    monkeypatch.setattr("app.services.github_ingestion.GitHubArtifactClient.fetch_artifact", fake_fetch_artifact)

    response = client.post(
        "/api/v1/documents/ingest/github",
        json={
            "owner": "example",
            "repo": "ops",
            "artifact_type": "commit",
            "commit_sha": "abc1234",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "queued"
    assert payload["job_id"].startswith("job-")

    job_response = client.get(f"/api/v1/documents/jobs/{payload['job_id']}")
    assert job_response.status_code == 200
    assert job_response.json()["status"] == "completed"


def test_github_ingested_commit_is_retrievable(monkeypatch) -> None:
    def fake_fetch_artifact(self, request):
        return GitHubArtifact(
            title="ops commit abc1234",
            content="Commit message: Fix login rollback handling and update health checks for the deployment workflow.",
            source_url="https://github.com/example/ops/commit/abc1234",
        )

    monkeypatch.setattr("app.services.github_ingestion.GitHubArtifactClient.fetch_artifact", fake_fetch_artifact)

    ingest_response = client.post(
        "/api/v1/documents/ingest/github",
        json={
            "owner": "example",
            "repo": "ops",
            "artifact_type": "commit",
            "commit_sha": "abc1234",
        },
    )
    assert ingest_response.status_code == 202

    chat_response = client.post(
        "/api/v1/chat",
        json={"message": "What changed in the login rollback handling commit?"},
    )

    assert chat_response.status_code == 200
    payload = chat_response.json()
    assert payload["citations"]
    assert "rollback handling" in payload["message"].lower()


def test_github_file_ingest_requires_path() -> None:
    response = client.post(
        "/api/v1/documents/ingest/github",
        json={
            "owner": "example",
            "repo": "ops",
            "artifact_type": "file",
        },
    )

    assert response.status_code == 422


def test_ingestion_job_listing_includes_recent_job() -> None:
    response = client.post(
        "/api/v1/documents/ingest",
        json={
            "title": "Deploy Notes",
            "content": "Deploy notes with rollback and health check validation.",
        },
    )
    assert response.status_code == 202

    jobs_response = client.get("/api/v1/documents/jobs")
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()
    assert jobs
    assert jobs[0]["job_id"] == response.json()["job_id"]
