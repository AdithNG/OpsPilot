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
