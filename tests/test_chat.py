from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_returns_citation_for_runbook_question() -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "What does the deployment runbook say about rollback?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "question"
    assert payload["citations"]
    assert payload["requires_approval"] is False


def test_chat_requires_approval_for_write_like_actions() -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "Create a Jira ticket for this production issue."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "action_request"
    assert payload["requires_approval"] is True
    assert payload["approval"]["request_id"].startswith("approval-")
