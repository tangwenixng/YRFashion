from uuid import uuid4

from fastapi.testclient import TestClient

from backend.db.session import SessionLocal
from backend.main import app
from backend.models import Message, MiniappUser, Product


def seed_product() -> int:
    return seed_products(1)[0]


def seed_products(count: int = 2) -> list[int]:
    product_ids: list[int] = []
    with SessionLocal() as db:
        for _ in range(count):
            product = Product(
                name=f"Bag-{uuid4().hex[:8]}",
                description="product for message submit",
                tags_json=["bag"],
                status="published",
                sort_order=0,
            )
            db.add(product)
            db.flush()
            product_ids.append(product.id)
        db.commit()
        return product_ids


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
    assert payload["items"][1]["product_name"]
    assert payload["items"][1]["reply_content"] == "建议搭配短靴和针织上衣。"
    assert all(item["product_id"] == product_id for item in payload["items"])

    with SessionLocal() as db:
        messages = db.query(Message).filter(Message.miniapp_user_id == miniapp_user_id).all()
        assert len(messages) == 2


def test_message_submit_uses_updated_miniapp_profile() -> None:
    product_id = seed_product()

    with TestClient(app) as client:
        headers, miniapp_user_id = get_miniapp_headers(client)
        profile_response = client.put(
            "/api/miniapp/auth/profile",
            headers=headers,
            json={
                "nickname": "头像用户",
                "avatar_url": "https://cdn.example.com/avatars/message-user.jpg",
            },
        )
        assert profile_response.status_code == 200

        response = client.post(
            f"/api/miniapp/products/{product_id}/messages",
            headers=headers,
            json={"content": "帮我看看这款有现货吗？"},
        )

    assert response.status_code == 201

    with SessionLocal() as db:
        user = db.get(MiniappUser, miniapp_user_id)
        assert user is not None
        assert user.nickname == "头像用户"
        assert user.avatar_url == "https://cdn.example.com/avatars/message-user.jpg"


def test_message_history_endpoint_supports_all_messages_and_product_filter() -> None:
    first_product_id, second_product_id = seed_products(2)

    with TestClient(app) as client:
        headers, _ = get_miniapp_headers(client)

        first_response = client.post(
            f"/api/miniapp/products/{first_product_id}/messages",
            headers=headers,
            json={"content": "First product question."},
        )
        second_response = client.post(
            f"/api/miniapp/products/{second_product_id}/messages",
            headers=headers,
            json={"content": "Second product question."},
        )
        assert first_response.status_code == 201
        assert second_response.status_code == 201

        all_response = client.get("/api/miniapp/messages?page=1&page_size=10", headers=headers)
        filtered_response = client.get(
            f"/api/miniapp/messages?product_id={first_product_id}&page=1&page_size=10",
            headers=headers,
        )

    assert all_response.status_code == 200
    all_payload = all_response.json()
    assert all_payload["total"] == 2
    assert {item["product_id"] for item in all_payload["items"]} == {first_product_id, second_product_id}
    assert all(item["product_name"] for item in all_payload["items"])

    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    assert filtered_payload["total"] == 1
    assert [item["product_id"] for item in filtered_payload["items"]] == [first_product_id]
