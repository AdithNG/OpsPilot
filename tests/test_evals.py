from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_eval_summary_scores_recent_traces() -> None:
    client.post("/api/v1/chat", json={"message": "What does the rollback runbook say?"})
    client.post("/api/v1/chat", json={"message": "Summarize this incident"})

    response = client.get("/api/v1/evals/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_traces"] >= 2
    assert payload["average_score"] > 0
    assert payload["evaluations"]


def test_trace_eval_returns_expected_result() -> None:
    chat_response = client.post(
        "/api/v1/chat",
        json={"message": "Create a Jira ticket for this production issue."},
    )
    trace_id = chat_response.json()["trace"]["trace_id"]

    response = client.get(f"/api/v1/evals/traces/{trace_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_id"] == trace_id
    assert payload["passed"] is True
    assert any("approval behavior" in check for check in payload["checks"])


def test_trace_eval_returns_not_found_for_missing_trace() -> None:
    response = client.get("/api/v1/evals/traces/trace-missing")

    assert response.status_code == 404
