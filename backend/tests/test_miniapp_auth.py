import time
from io import BytesIO

from fastapi.testclient import TestClient

from backend.db.session import SessionLocal
from backend.main import app
from backend.models import MiniappUser


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
    assert (
        second_response.json()["user"]["last_visit_at"]
        >= first_response.json()["user"]["last_visit_at"]
    )


def test_miniapp_profile_update_persists_nickname_and_avatar() -> None:
    with TestClient(app) as client:
        login_response = client.post("/api/miniapp/auth/login", json={"code": "profile-code-001"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        update_response = client.put(
            "/api/miniapp/auth/profile",
            headers=headers,
            json={
                "nickname": "留言顾客",
                "avatar_url": "https://cdn.example.com/avatars/customer-1.jpg",
            },
        )

    assert update_response.status_code == 200
    payload = update_response.json()
    assert payload["nickname"] == "留言顾客"
    assert payload["avatar_url"] is None
    assert payload["pending_avatar_url"] == "https://cdn.example.com/avatars/customer-1.jpg"
    assert payload["avatar_review_status"] == "pending"

    with SessionLocal() as db:
        user = db.get(MiniappUser, payload["id"])
        assert user is not None
        assert user.nickname == "留言顾客"
        assert user.avatar_url is None
        assert user.pending_avatar_url == "https://cdn.example.com/avatars/customer-1.jpg"
        assert user.avatar_review_status == "pending"


def test_miniapp_avatar_upload_marks_avatar_as_pending() -> None:
    with TestClient(app) as client:
        login_response = client.post("/api/miniapp/auth/login", json={"code": "profile-code-002"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        upload_response = client.post(
            "/api/miniapp/auth/avatar",
            headers=headers,
            files={"file": ("avatar.png", BytesIO(b"\x89PNG\r\n\x1a\navatar"), "image/png")},
        )

    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["avatar_url"].startswith("/uploads/miniapp-users/")
    assert payload["pending_avatar_url"] == payload["avatar_url"]
    assert payload["avatar_review_status"] == "pending"


def test_miniapp_profile_rejects_high_risk_nickname() -> None:
    with TestClient(app) as client:
        login_response = client.post("/api/miniapp/auth/login", json={"code": "profile-code-003"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        update_response = client.put(
            "/api/miniapp/auth/profile",
            headers=headers,
            json={
                "nickname": "加微信领券",
                "avatar_url": "https://cdn.example.com/avatars/customer-3.jpg",
            },
        )

    assert update_response.status_code == 400
    assert update_response.json()["detail"] == "昵称包含高风险内容，请修改后再提交"
