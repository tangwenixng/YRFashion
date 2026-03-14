import time

from fastapi.testclient import TestClient

from backend.main import app


def test_miniapp_login_creates_user_and_returns_token() -> None:
    with TestClient(app) as client:
        response = client.post("/api/miniapp/auth/login", json={"code": "miniapp-code-001"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["user"]["id"] > 0


def test_miniapp_login_reuses_existing_user() -> None:
    with TestClient(app) as client:
        first_response = client.post("/api/miniapp/auth/login", json={"code": "same-code"})
        time.sleep(0.01)
        second_response = client.post("/api/miniapp/auth/login", json={"code": "same-code"})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["user"]["id"] == second_response.json()["user"]["id"]
    assert second_response.json()["user"]["last_visit_at"] >= first_response.json()["user"]["last_visit_at"]
