from functools import lru_cache
from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from backend.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


def save_product_image(product_id: int, upload: UploadFile) -> tuple[str, str]:
    content = _read_and_validate_upload(upload)
    extension = Path(upload.filename or "upload.bin").suffix.lower() or ".bin"
    relative_path = _build_product_image_key(product_id, extension)
    content_type = upload.content_type or "application/octet-stream"

    if settings.uses_cloud_storage:
        image_url = _save_cloud_file(relative_path, content, content_type)
    else:
        image_url = _save_local_file(relative_path, content)

    return relative_path, image_url


def delete_product_image_file(storage_path: str) -> None:
    if not storage_path:
        return

    if settings.uses_cloud_storage:
        _delete_cloud_file(storage_path)
        return

    absolute_path = settings.resolved_upload_dir / storage_path
    absolute_path.unlink(missing_ok=True)


def _read_and_validate_upload(upload: UploadFile) -> bytes:
    if upload.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type",
        )

    content = upload.file.read()
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image exceeds 5MB limit",
        )

    return content


def _build_product_image_key(product_id: int, extension: str) -> str:
    relative_dir = PurePosixPath("products") / str(product_id)
    filename = f"{uuid4().hex}{extension}"
    relative_path = relative_dir / filename

    if settings.uses_cloud_storage and settings.resolved_storage_path_prefix:
        return str(PurePosixPath(settings.resolved_storage_path_prefix) / relative_path)

    return relative_path.as_posix()


def _save_local_file(relative_path: str, content: bytes) -> str:
    local_relative_path = PurePosixPath(relative_path)

    target_dir = settings.resolved_upload_dir / local_relative_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    absolute_path = settings.resolved_upload_dir / local_relative_path
    absolute_path.write_bytes(content)

    return f"/uploads/{local_relative_path.as_posix()}"


def _save_cloud_file(relative_path: str, content: bytes, content_type: str) -> str:
    client = _get_cos_client()
    client.put_object(
        Bucket=settings.storage_bucket,
        Body=content,
        Key=relative_path,
        ContentType=content_type,
    )
    return _build_cloud_public_url(relative_path)


def _delete_cloud_file(relative_path: str) -> None:
    try:
        client = _get_cos_client()
        client.delete_object(Bucket=settings.storage_bucket, Key=relative_path)
    except Exception:
        # Best-effort cleanup after DB deletion; avoid surfacing a secondary storage error here.
        return


def _build_cloud_public_url(relative_path: str) -> str:
    if settings.storage_public_base_url:
        base = settings.storage_public_base_url.rstrip("/")
        return f"{base}/{relative_path}"

    return (
        f"https://{settings.storage_bucket}.cos.{settings.storage_region}.myqcloud.com/{relative_path}"
    )


@lru_cache(maxsize=1)
def _get_cos_client():
    from qcloud_cos import CosConfig, CosS3Client

    config = CosConfig(
        Region=settings.storage_region,
        SecretId=settings.storage_secret_id,
        SecretKey=settings.storage_secret_key,
        Scheme="https",
    )
    return CosS3Client(config)
