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
