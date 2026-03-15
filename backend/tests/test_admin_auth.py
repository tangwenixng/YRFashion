from uuid import uuid4

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


def test_admin_account_management_and_change_password() -> None:
    username = f"editor-{uuid4().hex[:8]}"

    with TestClient(app) as client:
        login_response = client.post(
            "/api/admin/auth/login",
            json={"username": "admin", "password": "admin123456"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        create_response = client.post(
            "/api/admin/accounts",
            headers=headers,
            json={
                "username": username,
                "display_name": "运营同学",
                "password": "editor12345",
                "status": "active",
            },
        )
        assert create_response.status_code == 201
        admin_id = create_response.json()["id"]

        list_response = client.get("/api/admin/accounts", headers=headers)
        assert list_response.status_code == 200
        assert any(item["id"] == admin_id for item in list_response.json()["items"])

        disable_response = client.patch(
            f"/api/admin/accounts/{admin_id}",
            headers=headers,
            json={"status": "disabled"},
        )
        assert disable_response.status_code == 200
        assert disable_response.json()["status"] == "disabled"

        reset_password_response = client.post(
            f"/api/admin/accounts/{admin_id}/reset-password",
            headers=headers,
            json={"new_password": "editor99999"},
        )
        assert reset_password_response.status_code == 200

        disabled_login_response = client.post(
            "/api/admin/auth/login",
            json={"username": username, "password": "editor99999"},
        )
        assert disabled_login_response.status_code == 403

        activate_response = client.patch(
            f"/api/admin/accounts/{admin_id}",
            headers=headers,
            json={"status": "active", "display_name": "运营账号"},
        )
        assert activate_response.status_code == 200
        assert activate_response.json()["display_name"] == "运营账号"

        changed_password_response = client.post(
            "/api/admin/auth/change-password",
            headers=headers,
            json={
                "current_password": "admin123456",
                "new_password": "admin1234567",
            },
        )
        assert changed_password_response.status_code == 204

        relogin_response = client.post(
            "/api/admin/auth/login",
            json={"username": "admin", "password": "admin1234567"},
        )
        assert relogin_response.status_code == 200
        new_headers = {"Authorization": f"Bearer {relogin_response.json()['access_token']}"}

        restore_password_response = client.post(
            "/api/admin/auth/change-password",
            headers=new_headers,
            json={
                "current_password": "admin1234567",
                "new_password": "admin123456",
            },
        )
        assert restore_password_response.status_code == 204
