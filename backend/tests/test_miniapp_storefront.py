from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func

from backend.db.session import SessionLocal
from backend.main import app
from backend.models import Product, ProductImage, ShopSetting


def seed_storefront_data() -> tuple[int, int]:
    unique = uuid4().hex[:8]
    with SessionLocal() as db:
        current_min_sort = db.query(func.min(Product.sort_order)).scalar()
        anchor_sort = current_min_sort if current_min_sort is not None else 0

        setting = db.get(ShopSetting, 1)
        setting.shop_name = f"YRFasion-{unique}"
        setting.shop_intro = "精选穿搭与女装系列"
        setting.contact_phone = "18800001111"
        setting.wechat_id = "yrfasion-shop"
        setting.address = "上海市静安区南京西路"
        setting.business_hours = "10:00-21:00"
        setting.homepage_banner_json = ["/uploads/banner-a.jpg", "/uploads/banner-b.jpg"]
        db.add(setting)

        featured = Product(
            name=f"Dress-{unique}",
            description="featured product",
            tags_json=["featured", "spring"],
            status="published",
            sort_order=anchor_sort - 2,
        )
        another = Product(
            name=f"Skirt-{unique}",
            description="secondary product",
            tags_json=["daily"],
            status="published",
            sort_order=anchor_sort - 1,
        )
        hidden = Product(
            name=f"Hidden-{unique}",
            description="hidden product",
            tags_json=["draft"],
            status="draft",
            sort_order=anchor_sort - 3,
        )
        db.add_all([featured, another, hidden])
        db.commit()
        db.refresh(featured)
        db.refresh(another)

        db.add(
            ProductImage(
                product_id=featured.id,
                storage_type="local",
                storage_path=f"products/{featured.id}/cover.png",
                image_url="/uploads/products/featured-cover.png",
                original_name="cover.png",
                sort_order=0,
                is_cover=True,
            )
        )
        db.commit()
        return featured.id, another.id


def test_home_returns_storefront_content() -> None:
    featured_id, another_id = seed_storefront_data()

    with TestClient(app) as client:
        response = client.get("/api/miniapp/home")

    assert response.status_code == 200
    payload = response.json()
    featured_items = payload["featured_products"]
    featured_ids = [item["id"] for item in featured_items]
    assert payload["shop_name"].startswith("YRFasion-")
    assert payload["homepage_banner_urls"] == ["/uploads/banner-a.jpg", "/uploads/banner-b.jpg"]
    assert featured_ids[0] == featured_id
    assert another_id in featured_ids
    assert featured_items[0]["cover_image_url"] == f"/uploads/products/{featured_id}/cover.png"


def test_contact_returns_shop_contact_data() -> None:
    seed_storefront_data()

    with TestClient(app) as client:
        response = client.get("/api/miniapp/shop/contact")

    assert response.status_code == 200
    payload = response.json()
    assert payload["contact_phone"] == "18800001111"
    assert payload["wechat_id"] == "yrfasion-shop"
    assert payload["address"] == "上海市静安区南京西路"
