from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_api_key_protects_chat_endpoint() -> None:
    settings.api_key = "secret-token"

    unauthorized = client.post("/api/v1/chat", json={"message": "What does the rollback runbook say?"})
    authorized = client.post(
        "/api/v1/chat",
        json={"message": "What does the rollback runbook say?"},
        headers={"x-api-key": "secret-token"},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


def test_health_endpoint_remains_public_with_api_key_enabled() -> None:
    settings.api_key = "secret-token"

    response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_rate_limit_rejects_excess_requests() -> None:
    settings.rate_limit_requests = 2
    settings.rate_limit_window_seconds = 60

    first = client.get("/api/v1/observability/summary")
    second = client.get("/api/v1/observability/summary")
    third = client.get("/api/v1/observability/summary")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429


def test_cors_preflight_allows_frontend_origin_for_graphql() -> None:
    response = client.options(
        settings.graphql_path,
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
