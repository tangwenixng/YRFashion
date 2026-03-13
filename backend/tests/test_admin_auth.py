from fastapi.testclient import TestClient

from backend.main import app


def test_admin_login_and_me() -> None:
    with TestClient(app) as client:
        login_response = client.post(
            "/api/admin/auth/login",
            json={"username": "admin", "password": "admin123456"},
        )

        assert login_response.status_code == 200

        access_token = login_response.json()["access_token"]
        me_response = client.get(
            "/api/admin/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "admin"


def test_admin_login_rejects_bad_password() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/auth/login",
            json={"username": "admin", "password": "wrong-pass-1"},
        )

    assert response.status_code == 401
