from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ticket_request_creates_tool_execution() -> None:
    response = client.post(
        "/api/v1/chat",
        json={"message": "Draft a bug ticket for login failures after deploy"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tool_executions"]
    assert payload["tool_executions"][0]["tool_name"] == "ticket_drafter"
    assert payload["tool_executions"][0]["status"] == "completed"


def test_tool_execution_read_endpoints_return_recent_execution() -> None:
    chat_response = client.post(
        "/api/v1/chat",
        json={"message": "Summarize this incident from the outage notes"},
    )
    execution_id = chat_response.json()["tool_executions"][0]["execution_id"]

    list_response = client.get("/api/v1/tools/executions")
    get_response = client.get(f"/api/v1/tools/executions/{execution_id}")

    assert list_response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json()["execution_id"] == execution_id


def test_missing_tool_execution_returns_not_found() -> None:
    response = client.get("/api/v1/tools/executions/tool-missing")

    assert response.status_code == 404
