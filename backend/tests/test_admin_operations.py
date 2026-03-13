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


def seed_message() -> tuple[int, int]:
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
        return message.id, user.id


def test_message_workflow_and_dashboard() -> None:
    message_id, _ = seed_message()

    with TestClient(app) as client:
        headers = get_admin_headers(client)

        summary_response = client.get("/api/admin/dashboard/summary", headers=headers)
        assert summary_response.status_code == 200
        assert summary_response.json()["unread_message_count"] >= 1

        list_response = client.get("/api/admin/messages?status=unread", headers=headers)
        assert list_response.status_code == 200
        assert any(item["id"] == message_id for item in list_response.json()["items"])

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


def test_user_list_and_settings() -> None:
    _, user_id = seed_message()

    with TestClient(app) as client:
        headers = get_admin_headers(client)

        users_response = client.get("/api/admin/users", headers=headers)
        assert users_response.status_code == 200
        assert any(item["id"] == user_id for item in users_response.json()["items"])

        update_response = client.put(
            "/api/admin/settings",
            headers=headers,
            json={
                "shop_name": "YRFasion",
                "shop_intro": "Elegant fashion store",
                "contact_phone": "18800001111",
                "wechat_id": "yrfasion-shop",
                "address": "Shanghai",
                "business_hours": "10:00-21:00",
                "homepage_banner_urls": ["/uploads/banner-1.jpg"],
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["shop_name"] == "YRFasion"

        get_response = client.get("/api/admin/settings", headers=headers)

    assert get_response.status_code == 200
    assert get_response.json()["homepage_banner_urls"] == ["/uploads/banner-1.jpg"]
