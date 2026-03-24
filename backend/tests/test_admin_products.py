from io import BytesIO
# ruff: noqa: I001
from pathlib import Path
import struct
import zlib
from binascii import crc32
from uuid import uuid4

from fastapi.testclient import TestClient
from PIL import Image

from backend.core.config import settings
from backend.db.session import SessionLocal
from backend.main import app
from backend.models import Category


def get_admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/admin/auth/login",
        json={"username": "admin", "password": "admin123456"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def build_test_image_bytes(
    image_format: str = "PNG",
    size: tuple[int, int] = (64, 64),
    quality: int = 95,
) -> bytes:
    if image_format == "JPEG":
        image = Image.effect_noise(size, 96).convert("RGB")
    else:
        image = Image.new("RGB", size, color=(196, 164, 140))

    buffer = BytesIO()
    save_kwargs: dict[str, int] = {}
    if image_format == "JPEG":
        save_kwargs["quality"] = quality
    image.save(buffer, format=image_format, **save_kwargs)
    return buffer.getvalue()


def build_png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    chunk_payload = chunk_type + data
    return b"".join(
        (
            struct.pack("!I", len(data)),
            chunk_payload,
            struct.pack("!I", crc32(chunk_payload) & 0xFFFFFFFF),
        )
    )


def build_large_png_bytes(size: tuple[int, int] = (600, 600)) -> bytes:
    width, height = size
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend(
                (
                    (x * 13 + y * 7) % 256,
                    (x * 5 + y * 11) % 256,
                    (x * 17 + y * 3) % 256,
                )
            )

    compressed = zlib.compress(bytes(rows), level=0)
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            build_png_chunk(b"IHDR", ihdr),
            build_png_chunk(b"IDAT", compressed),
            build_png_chunk(b"IEND", b""),
        )
    )


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
            files={
                "file": ("look.png", BytesIO(build_test_image_bytes("PNG")), "image/png")
            },
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
            files={
                "file": ("cover.png", BytesIO(build_test_image_bytes("PNG")), "image/png")
            },
            data={"sort_order": "0", "is_cover": "true"},
        )
        second_upload_response = client.post(
            f"/api/admin/products/{product_id}/images",
            headers=headers,
            files={
                "file": ("detail.png", BytesIO(build_test_image_bytes("PNG")), "image/png")
            },
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
        assert any(
            image["id"] == second_image["id"] and image["is_cover"]
            for image in cover_images
        )

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


def test_product_delete_removes_product_and_local_images() -> None:
    product_name = f"Delete-{uuid4().hex[:8]}"

    with TestClient(app) as client:
        headers = get_admin_headers(client)
        create_response = client.post(
            "/api/admin/products",
            headers=headers,
            json={
                "name": product_name,
                "description": "delete me",
                "tags": ["winter"],
                "status": "published",
                "sort_order": 0,
            },
        )
        product_id = create_response.json()["id"]

        upload_response = client.post(
            f"/api/admin/products/{product_id}/images",
            headers=headers,
            files={
                "file": ("cover.png", BytesIO(build_test_image_bytes("PNG")), "image/png")
            },
            data={"sort_order": "0", "is_cover": "true"},
        )
        image_path = settings.resolved_upload_dir / Path(
            upload_response.json()["image_url"].removeprefix("/uploads/")
        )
        assert image_path.exists()

        delete_response = client.delete(f"/api/admin/products/{product_id}", headers=headers)
        list_response = client.get("/api/admin/products", headers=headers)

    assert delete_response.status_code == 204
    assert all(item["id"] != product_id for item in list_response.json()["items"])
    assert not image_path.exists()


def test_product_image_upload_auto_compresses_large_jpeg() -> None:
    product_name = f"Large-{uuid4().hex[:8]}"
    original_content = build_test_image_bytes("JPEG", size=(2400, 1800), quality=95)

    with TestClient(app) as client:
        headers = get_admin_headers(client)
        create_response = client.post(
            "/api/admin/products",
            headers=headers,
            json={
                "name": product_name,
                "description": "large image",
                "tags": [],
                "status": "draft",
                "sort_order": 0,
            },
        )
        product_id = create_response.json()["id"]

        upload_response = client.post(
            f"/api/admin/products/{product_id}/images",
            headers=headers,
            files={"file": ("large.jpg", BytesIO(original_content), "image/jpeg")},
            data={"sort_order": "0", "is_cover": "true"},
        )

    assert upload_response.status_code == 200
    image_path = settings.resolved_upload_dir / Path(
        upload_response.json()["image_url"].removeprefix("/uploads/")
    )
    assert image_path.exists()
    assert image_path.stat().st_size < len(original_content)

    with Image.open(image_path) as saved_image:
        assert max(saved_image.size) <= 1600


def test_product_image_upload_accepts_file_larger_than_default_multipart_part_limit() -> None:
    product_name = f"PartLimit-{uuid4().hex[:8]}"
    large_content = build_large_png_bytes()
    assert len(large_content) > 1024 * 1024

    with TestClient(app) as client:
        headers = get_admin_headers(client)
        create_response = client.post(
            "/api/admin/products",
            headers=headers,
            json={
                "name": product_name,
                "description": "multipart limit regression",
                "tags": [],
                "status": "draft",
                "sort_order": 0,
            },
        )
        product_id = create_response.json()["id"]

        upload_response = client.post(
            f"/api/admin/products/{product_id}/images",
            headers=headers,
            files={"file": ("part-limit.png", BytesIO(large_content), "image/png")},
            data={"sort_order": "0", "is_cover": "true"},
        )

    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["is_cover"] is True
    assert payload["image_url"].startswith("/uploads/products/")


def test_product_list_supports_filters_and_pagination() -> None:
    unique = uuid4().hex[:8]
    category_id: int

    with SessionLocal() as db:
        category = Category(name=f"Outerwear-{unique}", sort_order=1, status="active")
        db.add(category)
        db.commit()
        db.refresh(category)
        category_id = category.id

    with TestClient(app) as client:
        headers = get_admin_headers(client)
        first_response = client.post(
            "/api/admin/products",
            headers=headers,
            json={
                "name": f"Filter-Coat-{unique}",
                "category_id": category_id,
                "description": "spring outerwear",
                "tags": ["outerwear", "spring"],
                "status": "published",
                "sort_order": 1,
            },
        )
        second_response = client.post(
            "/api/admin/products",
            headers=headers,
            json={
                "name": f"Filter-Draft-{unique}",
                "description": "draft look",
                "tags": ["draft"],
                "status": "draft",
                "sort_order": 2,
            },
        )
        assert first_response.status_code == 201
        assert second_response.status_code == 201

        filtered_response = client.get(
            f"/api/admin/products?keyword=Coat-{unique}&status=published&category_id={category_id}&page=1&page_size=10",
            headers=headers,
        )
        paged_response = client.get(
            "/api/admin/products?page=1&page_size=1",
            headers=headers,
        )

    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    assert filtered_payload["total"] >= 1
    assert filtered_payload["page"] == 1
    assert filtered_payload["page_size"] == 10
    assert all(item["status"] == "published" for item in filtered_payload["items"])
    assert all(item["category_id"] == category_id for item in filtered_payload["items"])
    assert any(item["name"] == f"Filter-Coat-{unique}" for item in filtered_payload["items"])

    assert paged_response.status_code == 200
    paged_payload = paged_response.json()
    assert paged_payload["page"] == 1
    assert paged_payload["page_size"] == 1
    assert len(paged_payload["items"]) == 1


def test_product_batch_status_update() -> None:
    unique = uuid4().hex[:8]

    with TestClient(app) as client:
        headers = get_admin_headers(client)
        first_response = client.post(
            "/api/admin/products",
            headers=headers,
            json={
                "name": f"Batch-Coat-{unique}",
                "description": "batch publish target",
                "tags": ["outerwear"],
                "status": "draft",
                "sort_order": 1,
            },
        )
        second_response = client.post(
            "/api/admin/products",
            headers=headers,
            json={
                "name": f"Batch-Dress-{unique}",
                "description": "batch publish target",
                "tags": ["dress"],
                "status": "draft",
                "sort_order": 2,
            },
        )
        assert first_response.status_code == 201
        assert second_response.status_code == 201
        first_id = first_response.json()["id"]
        second_id = second_response.json()["id"]

        batch_response = client.post(
            "/api/admin/products/batch-status",
            headers=headers,
            json={"ids": [first_id, second_id], "status": "published"},
        )

    assert batch_response.status_code == 200
    payload = batch_response.json()
    assert payload["total"] == 2
    assert all(item["status"] == "published" for item in payload["items"])
