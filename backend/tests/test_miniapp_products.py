from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func

from backend.db.session import SessionLocal
from backend.main import app
from backend.models import Product, ProductImage


def seed_products() -> tuple[int, int, int]:
    unique = uuid4().hex[:8]
    with SessionLocal() as db:
        current_min_sort = db.query(func.min(Product.sort_order)).scalar()
        anchor_sort = current_min_sort if current_min_sort is not None else 0

        first = Product(
            name=f"Coat-{unique}",
            description="first published product",
            tags_json=["coat", "featured"],
            status="published",
            sort_order=anchor_sort - 2,
        )
        second = Product(
            name=f"Dress-{unique}",
            description="second published product",
            tags_json=["dress"],
            status="published",
            sort_order=anchor_sort - 1,
        )
        hidden = Product(
            name=f"Hidden-{unique}",
            description="draft product",
            tags_json=["hidden"],
            status="draft",
            sort_order=anchor_sort - 3,
        )
        db.add_all([first, second, hidden])
        db.commit()
        db.refresh(first)
        db.refresh(second)
        db.refresh(hidden)

        db.add_all(
            [
                ProductImage(
                    product_id=first.id,
                    storage_type="local",
                    storage_path=f"products/{first.id}/detail-b.png",
                    image_url="/uploads/products/detail-b.png",
                    original_name="detail-b.png",
                    sort_order=3,
                    is_cover=False,
                ),
                ProductImage(
                    product_id=first.id,
                    storage_type="local",
                    storage_path=f"products/{first.id}/cover-a.png",
                    image_url="/uploads/products/cover-a.png",
                    original_name="cover-a.png",
                    sort_order=1,
                    is_cover=True,
                ),
            ]
        )
        db.commit()
        return first.id, second.id, hidden.id


def test_product_list_returns_published_products_only() -> None:
    first_id, second_id, hidden_id = seed_products()

    with TestClient(app) as client:
        response = client.get("/api/miniapp/products?page=1&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    ids = [item["id"] for item in payload["items"]]
    assert first_id in ids
    assert second_id in ids
    assert hidden_id not in ids
    assert ids.index(first_id) < ids.index(second_id)
    assert payload["page"] == 1
    assert payload["page_size"] == 20


def test_product_detail_returns_sorted_images() -> None:
    first_id, _, hidden_id = seed_products()

    with TestClient(app) as client:
        response = client.get(f"/api/miniapp/products/{first_id}")
        hidden_response = client.get(f"/api/miniapp/products/{hidden_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == first_id
    assert payload["cover_image_url"] == "/uploads/products/cover-a.png"
    assert [item["image_url"] for item in payload["images"]] == [
        "/uploads/products/cover-a.png",
        "/uploads/products/detail-b.png",
    ]
    assert hidden_response.status_code == 404
