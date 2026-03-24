from functools import lru_cache
from io import BytesIO
from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError

from backend.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_DIMENSION = 1600
JPEG_SAVE_QUALITY = 82
WEBP_SAVE_QUALITY = 82


def save_product_image(product_id: int, upload: UploadFile) -> tuple[str, str]:
    content, extension, content_type = _read_and_prepare_upload(upload)
    relative_path = _build_product_image_key(product_id, extension)

    if settings.uses_cloud_storage:
        image_url = _save_cloud_file(relative_path, content, content_type)
    else:
        image_url = _save_local_file(relative_path, content)

    return relative_path, image_url


def save_miniapp_avatar(user_id: int, upload: UploadFile) -> tuple[str, str]:
    content, extension, content_type = _read_and_prepare_upload(upload)
    relative_path = _build_miniapp_avatar_key(user_id, extension)

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


def resolve_public_file_url(
    storage_type: str | None,
    storage_path: str | None,
    fallback_url: str | None = None,
) -> str:
    normalized_storage_type = (storage_type or "").strip().lower()
    normalized_storage_path = (storage_path or "").strip()

    if normalized_storage_type == "cloudbase" and normalized_storage_path:
        return _build_cloud_public_url(normalized_storage_path)

    if normalized_storage_type == "local" and normalized_storage_path:
        return _build_local_public_url(normalized_storage_path)

    if normalized_storage_path.startswith("/uploads/"):
        return normalized_storage_path

    return (fallback_url or "").strip()


def _read_and_prepare_upload(upload: UploadFile) -> tuple[bytes, str, str]:
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

    try:
        optimized_content, extension, content_type = _optimize_image_content(
            content,
            upload.content_type,
            Path(upload.filename or "").suffix.lower(),
        )
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image content",
        ) from exc

    return optimized_content, extension, content_type


def _optimize_image_content(
    content: bytes,
    content_type: str,
    original_extension: str,
) -> tuple[bytes, str, str]:
    output_format, default_extension = _resolve_output_format(content_type)

    with Image.open(BytesIO(content)) as source_image:
        image = ImageOps.exif_transpose(source_image)

        image = _normalize_image_mode(image, output_format)
        resized = False
        if max(image.size) > MAX_IMAGE_DIMENSION:
            image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
            resized = True

        output = BytesIO()
        image.save(output, format=output_format, **_build_save_kwargs(output_format))
        optimized_content = output.getvalue()

    if not resized and len(optimized_content) >= len(content):
        return content, original_extension or default_extension, content_type

    return optimized_content, original_extension or default_extension, content_type


def _resolve_output_format(content_type: str) -> tuple[str, str]:
    if content_type == "image/png":
        return "PNG", ".png"
    if content_type == "image/webp":
        return "WEBP", ".webp"
    return "JPEG", ".jpg"


def _normalize_image_mode(image: Image.Image, output_format: str) -> Image.Image:
    if output_format == "JPEG":
        if image.mode not in {"RGB", "L"}:
            return image.convert("RGB")
        return image

    if output_format == "PNG":
        if image.mode in {"RGBA", "LA", "L", "RGB"}:
            return image
        if "transparency" in image.info:
            return image.convert("RGBA")
        return image.convert("RGB")

    if image.mode in {"RGB", "RGBA", "L", "LA"}:
        return image
    if "transparency" in image.info:
        return image.convert("RGBA")
    return image.convert("RGB")


def _build_save_kwargs(output_format: str) -> dict[str, int | bool]:
    if output_format == "PNG":
        return {
            "optimize": True,
            "compress_level": 9,
        }
    if output_format == "WEBP":
        return {
            "quality": WEBP_SAVE_QUALITY,
            "method": 6,
        }
    return {
        "quality": JPEG_SAVE_QUALITY,
        "optimize": True,
        "progressive": True,
    }


def _build_product_image_key(product_id: int, extension: str) -> str:
    relative_dir = PurePosixPath("products") / str(product_id)
    filename = f"{uuid4().hex}{extension}"
    relative_path = relative_dir / filename

    if settings.uses_cloud_storage and settings.resolved_storage_path_prefix:
        return str(PurePosixPath(settings.resolved_storage_path_prefix) / relative_path)

    return relative_path.as_posix()


def _build_miniapp_avatar_key(user_id: int, extension: str) -> str:
    relative_dir = PurePosixPath("miniapp-users") / str(user_id) / "avatars"
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


def _build_local_public_url(relative_path: str) -> str:
    normalized_path = relative_path.strip()
    if normalized_path.startswith("/uploads/"):
        return normalized_path
    if normalized_path.startswith("uploads/"):
        return f"/{normalized_path}"
    return f"/uploads/{normalized_path.lstrip('/')}"


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

    if settings.storage_bucket:
        return f"https://{settings.storage_bucket}.tcb.qcloud.la/{relative_path}"

    return f"https://{settings.storage_bucket}.cos.{settings.storage_region}.myqcloud.com/{relative_path}"


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
