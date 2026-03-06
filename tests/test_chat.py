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
    assert payload["conversation_id"].startswith("conv-")
    assert payload["intent"] == "question"
    assert payload["citations"]
    assert payload["requires_approval"] is False
    assert payload["trace"]["steps"] == ["classify", "retrieve", "respond_question"]


def test_chat_returns_ingested_document_context() -> None:
    ingest_response = client.post(
        "/api/v1/documents/ingest",
        json={
            "title": "Kafka Runbook",
            "content": "Kafka consumer lag should be reduced by scaling consumers and checking partition skew.",
        },
    )
    assert ingest_response.status_code == 202

    response = client.post(
        "/api/v1/chat",
        json={"message": "What does the Kafka runbook say about consumer lag?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["citations"]
    assert "consumer lag" in payload["message"].lower()
    assert payload["trace"]["conversation_id"] == payload["conversation_id"]


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
    assert payload["trace"]["requires_approval"] is True


def test_chat_drafts_ticket_response() -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "Draft a bug ticket for login failures after deploy"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "ticket_draft"
    assert "acceptance criteria" in payload["message"].lower()
    assert payload["ticket_draft"]["title"]
    assert payload["ticket_draft"]["acceptance_criteria"]
    assert payload["incident_summary"] is None
    assert payload["trace"]["steps"][-1] == "draft_ticket"


def test_chat_returns_structured_incident_summary() -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "Summarize this incident from the outage notes"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "incident_summary"
    assert payload["incident_summary"]["severity"] == "sev2"
    assert len(payload["incident_summary"]["next_steps"]) >= 1
    assert payload["ticket_draft"] is None
    assert payload["trace"]["steps"][-1] == "summarize_incident"


def test_chat_reuses_existing_conversation_id() -> None:
    first = client.post("/api/v1/chat", json={"message": "What does the rollback runbook say?"})
    conversation_id = first.json()["conversation_id"]

    second = client.post(
        "/api/v1/chat",
        json={
            "message": "Draft a bug ticket for the rollback issue",
            "conversation_id": conversation_id,
        },
    )

    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id
