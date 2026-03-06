from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_approval_decision_round_trip() -> None:
    chat_response = client.post(
        "/api/v1/chat",
        json={"message": "Create a Jira ticket for this incident"},
    )
    request_id = chat_response.json()["approval"]["request_id"]

    decision_response = client.post(
        f"/api/v1/approvals/{request_id}/decision",
        json={"approved": True, "reviewer": "manager@example.com"},
    )

    assert decision_response.status_code == 200
    assert decision_response.json()["status"] == "approved"
    assert decision_response.json()["reviewer"] == "manager@example.com"


def test_list_approvals_shows_pending_request() -> None:
    chat_response = client.post(
        "/api/v1/chat",
        json={"message": "Create a Jira ticket for this incident"},
    )
    request_id = chat_response.json()["approval"]["request_id"]

    list_response = client.get("/api/v1/approvals")

    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload[0]["request_id"] == request_id
    assert payload[0]["status"] == "pending"


def test_get_approval_returns_updated_state() -> None:
    chat_response = client.post(
        "/api/v1/chat",
        json={"message": "Create a Jira ticket for this incident"},
    )
    request_id = chat_response.json()["approval"]["request_id"]

    client.post(
        f"/api/v1/approvals/{request_id}/decision",
        json={"approved": False, "reviewer": "manager@example.com", "note": "Need more context"},
    )
    get_response = client.get(f"/api/v1/approvals/{request_id}")

    assert get_response.status_code == 200
    payload = get_response.json()
    assert payload["status"] == "rejected"
    assert payload["note"] == "Need more context"
