from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func

from backend.db.session import SessionLocal
from backend.main import app
from backend.models import Category, Product, ProductImage


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


def seed_products_with_categories() -> tuple[int, int, int]:
    unique = uuid4().hex[:8]
    with SessionLocal() as db:
        active_category = Category(
            name=f"Outerwear-{unique}",
            sort_order=-2,
            status="active",
        )
        disabled_category = Category(
            name=f"Archive-{unique}",
            sort_order=-1,
            status="disabled",
        )
        db.add_all([active_category, disabled_category])
        db.commit()
        db.refresh(active_category)
        db.refresh(disabled_category)

        active_product = Product(
            name=f"Jacket-{unique}",
            category_id=active_category.id,
            description="active category product",
            tags_json=["outerwear"],
            status="published",
            sort_order=-2,
        )
        disabled_product = Product(
            name=f"Skirt-{unique}",
            category_id=disabled_category.id,
            description="disabled category product",
            tags_json=["archive"],
            status="published",
            sort_order=-1,
        )
        uncategorized_product = Product(
            name=f"Scarf-{unique}",
            description="uncategorized product",
            tags_json=["scarf"],
            status="published",
            sort_order=0,
        )
        db.add_all([active_product, disabled_product, uncategorized_product])
        db.commit()
        db.refresh(active_product)
        db.refresh(disabled_product)
        db.refresh(uncategorized_product)

        return active_category.id, disabled_category.id, active_product.id


def seed_products_with_related() -> tuple[int, int, int, int]:
    unique = uuid4().hex[:8]
    with SessionLocal() as db:
        category = Category(
            name=f"Recommend-{unique}",
            sort_order=-5,
            status="active",
        )
        other_category = Category(
            name=f"Other-{unique}",
            sort_order=-4,
            status="active",
        )
        db.add_all([category, other_category])
        db.commit()
        db.refresh(category)
        db.refresh(other_category)

        target = Product(
            name=f"Blazer-{unique}",
            category_id=category.id,
            description="target product",
            tags_json=["blazer", "spring"],
            status="published",
            sort_order=-4,
        )
        same_category = Product(
            name=f"Coat-{unique}",
            category_id=category.id,
            description="same category related",
            tags_json=["coat", "spring"],
            status="published",
            sort_order=-3,
        )
        same_tag = Product(
            name=f"Knit-{unique}",
            category_id=other_category.id,
            description="same tag related",
            tags_json=["spring", "knit"],
            status="published",
            sort_order=-2,
        )
        fallback = Product(
            name=f"Scarf-{unique}",
            category_id=other_category.id,
            description="fallback related",
            tags_json=["scarf"],
            status="published",
            sort_order=-1,
        )
        db.add_all([target, same_category, same_tag, fallback])
        db.commit()
        db.refresh(target)
        db.refresh(same_category)
        db.refresh(same_tag)
        db.refresh(fallback)

        return target.id, same_category.id, same_tag.id, fallback.id


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
    assert payload["cover_image_url"] == f"/uploads/products/{first_id}/cover-a.png"
    assert [item["image_url"] for item in payload["images"]] == [
        f"/uploads/products/{first_id}/cover-a.png",
        f"/uploads/products/{first_id}/detail-b.png",
    ]
    assert hidden_response.status_code == 404


def test_product_detail_returns_related_products() -> None:
    target_id, same_category_id, same_tag_id, fallback_id = seed_products_with_related()

    with TestClient(app) as client:
        response = client.get(f"/api/miniapp/products/{target_id}")

    assert response.status_code == 200
    payload = response.json()
    related_ids = [item["id"] for item in payload["related_products"]]
    assert same_category_id in related_ids
    assert same_tag_id in related_ids
    assert fallback_id in related_ids
    assert target_id not in related_ids
    assert related_ids.index(same_category_id) < related_ids.index(same_tag_id)


def test_product_list_supports_category_filter_and_active_category_list() -> None:
    active_category_id, disabled_category_id, active_product_id = seed_products_with_categories()

    with TestClient(app) as client:
        categories_response = client.get("/api/miniapp/categories")
        filtered_response = client.get(f"/api/miniapp/products?category_id={active_category_id}")
        disabled_filtered_response = client.get(
            f"/api/miniapp/products?category_id={disabled_category_id}"
        )

    assert categories_response.status_code == 200
    categories_payload = categories_response.json()
    category_ids = [item["id"] for item in categories_payload["items"]]
    assert active_category_id in category_ids
    assert disabled_category_id not in category_ids

    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    assert [item["id"] for item in filtered_payload["items"]] == [active_product_id]
    assert filtered_payload["total"] == 1
    assert filtered_payload["has_more"] is False

    assert disabled_filtered_response.status_code == 200
    disabled_filtered_payload = disabled_filtered_response.json()
    assert disabled_filtered_payload["items"] == []
    assert disabled_filtered_payload["total"] == 0


def test_product_list_supports_keyword_search() -> None:
    first_id, second_id, _ = seed_products()

    with TestClient(app) as client:
        name_response = client.get("/api/miniapp/products?keyword=Coat")
        tag_response = client.get("/api/miniapp/products?keyword=dress")

    assert name_response.status_code == 200
    name_payload = name_response.json()
    assert [item["id"] for item in name_payload["items"]] == [first_id]

    assert tag_response.status_code == 200
    tag_payload = tag_response.json()
    assert [item["id"] for item in tag_payload["items"]] == [second_id]
