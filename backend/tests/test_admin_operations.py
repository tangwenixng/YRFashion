from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.db.session import SessionLocal
from backend.main import app
from backend.models import Message, MiniappUser, Product


def get_admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/admin/auth/login",
        json={"username": "admin", "password": "admin123456"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def seed_message() -> tuple[int, int, int]:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        user = MiniappUser(
            openid=f"openid-{uuid4().hex[:10]}",
            nickname="guest",
            unionid=None,
            avatar_url=None,
            first_visit_at=now,
            last_visit_at=now,
        )
        product = Product(
            name=f"Skirt-{uuid4().hex[:8]}",
            description="seed product",
            tags_json=[],
            status="published",
            sort_order=0,
        )
        db.add_all([user, product])
        db.commit()
        db.refresh(user)
        db.refresh(product)

        message = Message(
            product_id=product.id,
            miniapp_user_id=user.id,
            content="Is this available?",
            status="unread",
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message.id, user.id, product.id


def test_message_workflow_and_dashboard() -> None:
    message_id, _, product_id = seed_message()

    with TestClient(app) as client:
        headers = get_admin_headers(client)

        summary_response = client.get("/api/admin/dashboard/summary", headers=headers)
        assert summary_response.status_code == 200
        assert summary_response.json()["unread_message_count"] >= 1
        assert len(summary_response.json()["recent_message_trend"]) == 7
        assert isinstance(summary_response.json()["top_products"], list)

        list_response = client.get("/api/admin/messages?status=unread", headers=headers)
        assert list_response.status_code == 200
        assert list_response.json()["page"] == 1
        assert list_response.json()["page_size"] == 10
        assert any(item["id"] == message_id for item in list_response.json()["items"])

        filtered_response = client.get(
            f"/api/admin/messages?product_id={product_id}&page=1&page_size=10",
            headers=headers,
        )
        assert filtered_response.status_code == 200
        assert all(item["product_id"] == product_id for item in filtered_response.json()["items"])

        detail_response = client.get(f"/api/admin/messages/{message_id}", headers=headers)
        assert detail_response.status_code == 200
        assert detail_response.json()["id"] == message_id

        read_response = client.post(f"/api/admin/messages/{message_id}/read", headers=headers)
        assert read_response.status_code == 200
        assert read_response.json()["status"] == "read"

        unread_response = client.post(f"/api/admin/messages/{message_id}/unread", headers=headers)
        assert unread_response.status_code == 200
        assert unread_response.json()["status"] == "unread"

        reply_response = client.post(
            f"/api/admin/messages/{message_id}/reply",
            headers=headers,
            json={"reply_content": "Yes, available in store."},
        )

    assert reply_response.status_code == 200
    assert reply_response.json()["status"] == "replied"
    assert reply_response.json()["reply_content"] == "Yes, available in store."
    assert reply_response.json()["miniapp_user_avatar_url"] is None


def test_user_list_and_settings() -> None:
    _, user_id, _ = seed_message()

    with TestClient(app) as client:
        headers = get_admin_headers(client)

        users_response = client.get("/api/admin/users", headers=headers)
        assert users_response.status_code == 200
        assert users_response.json()["page"] == 1
        assert any(item["id"] == user_id for item in users_response.json()["items"])

        filtered_users_response = client.get(
            "/api/admin/users?keyword=guest&page=1&page_size=10&sort=last_visit_desc",
            headers=headers,
        )
        assert filtered_users_response.status_code == 200
        assert filtered_users_response.json()["page_size"] == 10
        assert any(item["id"] == user_id for item in filtered_users_response.json()["items"])

        update_response = client.put(
            "/api/admin/settings",
            headers=headers,
            json={
                "shop_name": "YRFasion",
                "shop_intro": "Elegant fashion store",
                "contact_intro": "欢迎分享你的穿搭想法或建议，我会在看到后尽快回复。",
                "contact_phone": "18800001111",
                "wechat_id": "yrfasion-shop",
                "address": "Shanghai",
                "business_hours": "10:00-21:00",
                "homepage_banner_urls": ["/uploads/banner-1.jpg"],
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["shop_name"] == "YRFasion"
        assert update_response.json()["has_unpublished_changes"] is True

        publish_response = client.post("/api/admin/settings/publish", headers=headers)
        assert publish_response.status_code == 200
        assert publish_response.json()["has_unpublished_changes"] is False

        get_response = client.get("/api/admin/settings", headers=headers)

    assert get_response.status_code == 200
    assert (
        get_response.json()["contact_intro"]
        == "欢迎分享你的穿搭想法或建议，我会在看到后尽快回复。"
    )
    assert get_response.json()["homepage_banner_urls"] == ["/uploads/banner-1.jpg"]
    assert get_response.json()["has_unpublished_changes"] is False


def test_avatar_review_workflow() -> None:
    with TestClient(app) as client:
        login_response = client.post("/api/miniapp/auth/login", json={"code": "avatar-review-user"})
        token = login_response.json()["access_token"]
        miniapp_headers = {"Authorization": f"Bearer {token}"}
        update_response = client.put(
            "/api/miniapp/auth/profile",
            headers=miniapp_headers,
            json={
                "nickname": "审核头像用户",
                "avatar_url": "https://cdn.example.com/avatars/review-user.jpg",
            },
        )
        assert update_response.status_code == 200
        user_id = update_response.json()["id"]

        headers = get_admin_headers(client)
        pending_list_response = client.get(
            "/api/admin/users?avatar_review_status=pending&page=1&page_size=10",
            headers=headers,
        )
        assert pending_list_response.status_code == 200
        assert any(item["id"] == user_id for item in pending_list_response.json()["items"])

        reject_response = client.post(
            f"/api/admin/users/{user_id}/avatar/reject",
            headers=headers,
            json={"reason": "头像包含不清晰人物主体，请重新上传"},
        )
        assert reject_response.status_code == 200
        assert reject_response.json()["avatar_review_status"] == "rejected"
        assert (
            reject_response.json()["avatar_reject_reason"]
            == "头像包含不清晰人物主体，请重新上传"
        )

        second_update_response = client.put(
            "/api/miniapp/auth/profile",
            headers=miniapp_headers,
            json={
                "nickname": "审核头像用户",
                "avatar_url": "https://cdn.example.com/avatars/review-user-approved.jpg",
            },
        )
        assert second_update_response.status_code == 200
        assert second_update_response.json()["avatar_review_status"] == "pending"

        approve_response = client.post(
            f"/api/admin/users/{user_id}/avatar/approve",
            headers=headers,
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["avatar_review_status"] == "approved"
        assert (
            approve_response.json()["avatar_url"]
            == "https://cdn.example.com/avatars/review-user-approved.jpg"
        )
        assert approve_response.json()["pending_avatar_url"] is None


def test_message_batch_read() -> None:
    first_message_id, _, _ = seed_message()
    second_message_id, _, _ = seed_message()

    with TestClient(app) as client:
        headers = get_admin_headers(client)
        batch_response = client.post(
            "/api/admin/messages/batch-read",
            headers=headers,
            json={"ids": [first_message_id, second_message_id]},
        )

    assert batch_response.status_code == 200
    payload = batch_response.json()
    assert payload["total"] == 2
    assert all(item["status"] == "read" for item in payload["items"])
