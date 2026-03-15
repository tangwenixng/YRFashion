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


def seed_unread_message() -> None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        user = MiniappUser(
            openid=f"notify-{uuid4().hex[:10]}",
            nickname="notify-user",
            unionid=None,
            avatar_url=None,
            first_visit_at=now,
            last_visit_at=now,
        )
        product = Product(
            name=f"Notify-{uuid4().hex[:8]}",
            description="notify product",
            tags_json=[],
            status="published",
            sort_order=0,
        )
        db.add_all([user, product])
        db.commit()
        db.refresh(user)
        db.refresh(product)
        db.add(
            Message(
                product_id=product.id,
                miniapp_user_id=user.id,
                content="Please notify me",
                status="unread",
            )
        )
        db.commit()


def test_notification_settings_and_send(monkeypatch) -> None:
    sent_messages: list[str] = []

    def fake_send(setting, text: str) -> None:
        sent_messages.append(f"{setting.channel}:{text}")

    monkeypatch.setattr("backend.api.routes.admin_notifications.send_webhook_message", fake_send)
    seed_unread_message()

    with TestClient(app) as client:
        headers = get_admin_headers(client)

        update_response = client.put(
            "/api/admin/notifications/settings",
            headers=headers,
            json={
                "enabled": True,
                "channel": "wecom",
                "webhook_url": "https://example.com/webhook",
                "message_prefix": "MVP",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["enabled"] is True

        get_response = client.get("/api/admin/notifications/settings", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["channel"] == "wecom"

        test_response = client.post("/api/admin/notifications/test", headers=headers)
        assert test_response.status_code == 200

        summary_response = client.post("/api/admin/notifications/unread-summary", headers=headers)
        assert summary_response.status_code == 200

        dashboard_response = client.get("/api/admin/dashboard/summary", headers=headers)

    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["notification_enabled"] is True
    assert dashboard_response.json()["notification_channel"] == "wecom"
    assert len(dashboard_response.json()["recent_message_trend"]) == 7
    assert isinstance(dashboard_response.json()["top_products"], list)
    assert len(sent_messages) == 2
    assert "Webhook 通道已连通" in sent_messages[0]
    assert "当前未读留言" in sent_messages[1]
