from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def build_token_subject(subject: str, scope: str | None = None) -> str:
    if scope is None:
        return subject
    return f"{scope}:{subject}"


def extract_token_subject(
    payload: dict[str, Any],
    *,
    expected_scope: str | None = None,
    allow_unscoped: bool = False,
) -> str | None:
    raw_subject = payload.get("sub")
    if not isinstance(raw_subject, str) or not raw_subject:
        return None

    if ":" not in raw_subject:
        if expected_scope is None or allow_unscoped:
            return raw_subject
        return None

    scope, subject = raw_subject.split(":", 1)
    if not subject:
        return None
    if expected_scope is not None and scope != expected_scope:
        return None
    return subject


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    *,
    scope: str | None = None,
) -> str:
    expires_at = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": build_token_subject(subject, scope), "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
