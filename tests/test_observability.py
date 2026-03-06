from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_observability_summary_reports_activity() -> None:
    client.post("/api/v1/chat", json={"message": "What does the rollback runbook say?"})
    client.post("/api/v1/chat", json={"message": "Draft a bug ticket for the rollback issue"})

    response = client.get("/api/v1/observability/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["storage_backend"] == "memory"
    assert payload["conversation_count"] >= 2
    assert payload["trace_count"] >= 2
    assert payload["document_count"] >= 1
    assert payload["recent_traces"]


def test_observability_summary_orders_recent_traces_newest_first() -> None:
    first = client.post("/api/v1/chat", json={"message": "What does the rollback runbook say?"}).json()
    second = client.post("/api/v1/chat", json={"message": "Summarize this incident"}).json()

    response = client.get("/api/v1/observability/summary")

    assert response.status_code == 200
    recent_traces = response.json()["recent_traces"]
    assert recent_traces[0]["trace_id"] == second["trace"]["trace_id"]
    assert recent_traces[1]["trace_id"] == first["trace"]["trace_id"]
