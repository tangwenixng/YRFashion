from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import app


def get_admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/admin/auth/login",
        json={"username": "admin", "password": "admin123456"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_category_crud_and_product_category_name() -> None:
    category_name = f"Outerwear-{uuid4().hex[:8]}"
    product_name = f"Coat-{uuid4().hex[:8]}"

    with TestClient(app) as client:
        headers = get_admin_headers(client)

        create_category_response = client.post(
            "/api/admin/categories",
            headers=headers,
            json={
                "name": category_name,
                "sort_order": 12,
                "status": "active",
            },
        )
        assert create_category_response.status_code == 201
        category_id = create_category_response.json()["id"]

        update_category_response = client.put(
            f"/api/admin/categories/{category_id}",
            headers=headers,
            json={
                "name": f"{category_name}-updated",
                "sort_order": 6,
                "status": "active",
            },
        )
        assert update_category_response.status_code == 200
        assert update_category_response.json()["sort_order"] == 6

        status_response = client.put(
            f"/api/admin/categories/{category_id}/status",
            headers=headers,
            json={"status": "disabled"},
        )
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "disabled"

        product_response = client.post(
            "/api/admin/products",
            headers=headers,
            json={
                "name": product_name,
                "category_id": category_id,
                "description": "category test",
                "tags": ["mvp"],
                "status": "draft",
                "sort_order": 1,
            },
        )
        assert product_response.status_code == 201
        assert product_response.json()["category_name"] == f"{category_name}-updated"

        list_categories_response = client.get("/api/admin/categories", headers=headers)
        assert list_categories_response.status_code == 200
        assert any(
            item["id"] == category_id and item["product_count"] >= 1
            for item in list_categories_response.json()["items"]
        )
