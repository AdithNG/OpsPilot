from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_page_loads() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "OpsPilot Demo" in response.text
