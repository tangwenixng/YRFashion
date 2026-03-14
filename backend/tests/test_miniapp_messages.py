from uuid import uuid4

from fastapi.testclient import TestClient

from backend.db.session import SessionLocal
from backend.main import app
from backend.models import Message, Product


def seed_product() -> int:
    with SessionLocal() as db:
        product = Product(
            name=f"Bag-{uuid4().hex[:8]}",
            description="product for message submit",
            tags_json=["bag"],
            status="published",
            sort_order=0,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product.id


def get_miniapp_headers(client: TestClient) -> tuple[dict[str, str], int]:
    response = client.post("/api/miniapp/auth/login", json={"code": f"msg-{uuid4().hex}"})
    payload = response.json()
    return {"Authorization": f"Bearer {payload['access_token']}"}, payload["user"]["id"]


def test_message_submit_requires_login() -> None:
    product_id = seed_product()

    with TestClient(app) as client:
        response = client.post(
            f"/api/miniapp/products/{product_id}/messages",
            json={"content": "Is this in stock?"},
        )

    assert response.status_code == 401


def test_message_submit_creates_unread_message() -> None:
    product_id = seed_product()

    with TestClient(app) as client:
        headers, miniapp_user_id = get_miniapp_headers(client)
        response = client.post(
            f"/api/miniapp/products/{product_id}/messages",
            headers=headers,
            json={"content": "  Need size and fabric details.  "},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["product_id"] == product_id
    assert payload["miniapp_user_id"] == miniapp_user_id
    assert payload["content"] == "Need size and fabric details."
    assert payload["status"] == "unread"

    with SessionLocal() as db:
        message = db.get(Message, payload["id"])
        assert message is not None
        assert message.status == "unread"
        assert message.created_at is not None


def test_message_history_requires_login() -> None:
    product_id = seed_product()

    with TestClient(app) as client:
        response = client.get(f"/api/miniapp/products/{product_id}/messages")

    assert response.status_code == 401


def test_message_history_returns_current_user_messages_only() -> None:
    product_id = seed_product()

    with TestClient(app) as client:
        headers, miniapp_user_id = get_miniapp_headers(client)
        other_headers, _ = get_miniapp_headers(client)

        first_create = client.post(
            f"/api/miniapp/products/{product_id}/messages",
            headers=headers,
            json={"content": "Need sizing details."},
        )
        client.post(
            f"/api/miniapp/products/{product_id}/messages",
            headers=headers,
            json={"content": "Can you share styling advice?"},
        )
        client.post(
            f"/api/miniapp/products/{product_id}/messages",
            headers=other_headers,
            json={"content": "Other user question."},
        )

        with SessionLocal() as db:
            first_message = db.get(Message, first_create.json()["id"])
            first_message.status = "replied"
            first_message.reply_content = "建议搭配短靴和针织上衣。"
            db.add(first_message)
            db.commit()

        response = client.get(f"/api/miniapp/products/{product_id}/messages", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2
    assert [item["content"] for item in payload["items"]] == [
        "Can you share styling advice?",
        "Need sizing details.",
    ]
    assert payload["items"][1]["status"] == "replied"
    assert payload["items"][1]["reply_content"] == "建议搭配短靴和针织上衣。"
    assert all(item["product_id"] == product_id for item in payload["items"])

    with SessionLocal() as db:
        messages = db.query(Message).filter(Message.miniapp_user_id == miniapp_user_id).all()
        assert len(messages) == 2
