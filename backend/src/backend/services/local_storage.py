from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from backend.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


def save_product_image(product_id: int, upload: UploadFile) -> tuple[str, str]:
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

    extension = Path(upload.filename or "upload.bin").suffix.lower() or ".bin"
    relative_dir = Path("products") / str(product_id)
    target_dir = settings.resolved_upload_dir / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{extension}"
    relative_path = relative_dir / filename
    absolute_path = settings.resolved_upload_dir / relative_path
    absolute_path.write_bytes(content)

    image_url = f"/uploads/{relative_path.as_posix()}"
    return relative_path.as_posix(), image_url


def delete_local_file(storage_path: str) -> None:
    absolute_path = settings.resolved_upload_dir / storage_path
    absolute_path.unlink(missing_ok=True)
