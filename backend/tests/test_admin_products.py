from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.config import settings
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


def test_product_image_management() -> None:
    product_name = f"Look-{uuid4().hex[:8]}"

    with TestClient(app) as client:
        headers = get_admin_headers(client)
        create_response = client.post(
            "/api/admin/products",
            headers=headers,
            json={
                "name": product_name,
                "description": "look book",
                "tags": [],
                "status": "draft",
                "sort_order": 0,
            },
        )
        product_id = create_response.json()["id"]

        first_upload_response = client.post(
            f"/api/admin/products/{product_id}/images",
            headers=headers,
            files={"file": ("cover.png", BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
            data={"sort_order": "0", "is_cover": "true"},
        )
        second_upload_response = client.post(
            f"/api/admin/products/{product_id}/images",
            headers=headers,
            files={"file": ("detail.png", BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
            data={"sort_order": "3", "is_cover": "false"},
        )

        assert first_upload_response.status_code == 200
        assert second_upload_response.status_code == 200

        first_image = first_upload_response.json()
        second_image = second_upload_response.json()
        second_image_path = settings.resolved_upload_dir / Path(
            second_image["image_url"].removeprefix("/uploads/")
        )
        assert second_image_path.exists()

        cover_response = client.post(
            f"/api/admin/products/{product_id}/images/{second_image['id']}/cover",
            headers=headers,
        )
        assert cover_response.status_code == 200
        cover_images = cover_response.json()["images"]
        assert any(image["id"] == second_image["id"] and image["is_cover"] for image in cover_images)

        sort_response = client.put(
            f"/api/admin/products/{product_id}/images/sort",
            headers=headers,
            json={
                "items": [
                    {"id": first_image["id"], "sort_order": 5},
                    {"id": second_image["id"], "sort_order": 1},
                ]
            },
        )
        assert sort_response.status_code == 200
        sorted_images = sort_response.json()["images"]
        assert [image["id"] for image in sorted_images] == [second_image["id"], first_image["id"]]

        delete_response = client.delete(
            f"/api/admin/products/{product_id}/images/{second_image['id']}",
            headers=headers,
        )

    assert delete_response.status_code == 200
    remaining_images = delete_response.json()["images"]
    assert len(remaining_images) == 1
    assert remaining_images[0]["id"] == first_image["id"]
    assert remaining_images[0]["is_cover"] is True
    assert not second_image_path.exists()
