from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_conversation_returns_persisted_messages() -> None:
    chat_response = client.post(
        "/api/v1/chat",
        json={"message": "What does the deployment runbook say about rollback?"},
    )
    conversation_id = chat_response.json()["conversation_id"]

    response = client.get(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 200
    payload = response.json()
    assert [message["role"] for message in payload] == ["user", "assistant"]


def test_get_trace_returns_persisted_trace() -> None:
    chat_response = client.post(
        "/api/v1/chat",
        json={"message": "Draft a bug ticket for login failures after deploy"},
    )
    trace_id = chat_response.json()["trace"]["trace_id"]

    response = client.get(f"/api/v1/traces/{trace_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_id"] == trace_id
    assert payload["steps"][-1] == "draft_ticket"


def test_get_conversation_returns_not_found_for_unknown_id() -> None:
    response = client.get("/api/v1/conversations/conv-missing")

    assert response.status_code == 404


def test_get_trace_returns_not_found_for_unknown_id() -> None:
    response = client.get("/api/v1/traces/trace-missing")

    assert response.status_code == 404
