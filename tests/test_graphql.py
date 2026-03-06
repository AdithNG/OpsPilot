from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_graphql_health_query_returns_ok() -> None:
    response = client.post(
        settings.graphql_path,
        json={"query": "query { health }"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["health"] == "ok"


def test_graphql_chat_mutation_returns_grounded_response() -> None:
    response = client.post(
        settings.graphql_path,
        json={
            "query": """
                mutation Chat($message: String!) {
                  chat(message: $message) {
                    conversationId
                    intent
                    message
                    citations {
                      sourceId
                      title
                    }
                  }
                }
            """,
            "variables": {"message": "What does the deployment runbook say about rollback?"},
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]["chat"]
    assert payload["conversationId"].startswith("conv-")
    assert payload["intent"] == "question"
    assert payload["citations"]
    assert payload["citations"][0]["title"]


def test_graphql_respects_api_key_protection() -> None:
    settings.api_key = "secret-token"

    unauthorized = client.post(settings.graphql_path, json={"query": "query { health }"})
    authorized = client.post(
        settings.graphql_path,
        json={"query": "query { health }"},
        headers={"x-api-key": "secret-token"},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
