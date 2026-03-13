from io import BytesIO
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


def test_product_crud_and_sort() -> None:
    product_name = f"Coat-{uuid4().hex[:8]}"

    with TestClient(app) as client:
        headers = get_admin_headers(client)
        create_response = client.post(
            "/api/admin/products",
            headers=headers,
            json={
                "name": product_name,
                "description": "warm coat",
                "tags": ["winter", "new"],
                "status": "draft",
                "sort_order": 10,
            },
        )

        assert create_response.status_code == 201
        product_id = create_response.json()["id"]

        update_response = client.put(
            f"/api/admin/products/{product_id}",
            headers=headers,
            json={
                "name": product_name,
                "description": "updated coat",
                "tags": ["winter"],
                "status": "published",
                "sort_order": 5,
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "published"

        sort_response = client.put(
            f"/api/admin/products/{product_id}/sort",
            headers=headers,
            json={"sort_order": 1},
        )
        assert sort_response.status_code == 200
        assert sort_response.json()["sort_order"] == 1

        list_response = client.get("/api/admin/products", headers=headers)

    assert list_response.status_code == 200
    assert any(item["id"] == product_id for item in list_response.json()["items"])


def test_product_image_upload() -> None:
    product_name = f"Jacket-{uuid4().hex[:8]}"

    with TestClient(app) as client:
        headers = get_admin_headers(client)
        create_response = client.post(
            "/api/admin/products",
            headers=headers,
            json={
                "name": product_name,
                "description": "jacket",
                "tags": [],
                "status": "draft",
                "sort_order": 0,
            },
        )
        product_id = create_response.json()["id"]

        upload_response = client.post(
            f"/api/admin/products/{product_id}/images",
            headers=headers,
            files={"file": ("look.png", BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
            data={"sort_order": "0", "is_cover": "true"},
        )

    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["is_cover"] is True
    assert payload["image_url"].startswith("/uploads/products/")
