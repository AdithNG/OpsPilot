from fastapi.testclient import TestClient

from app.main import app

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
    assert payload["chunks_created"] >= 1
