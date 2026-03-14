from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.core.security import decode_token, extract_token_subject
from backend.db.session import get_db
from backend.models import AdminUser, MiniappUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/auth/login")
miniapp_bearer = HTTPBearer(auto_error=False)


def get_current_admin(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> AdminUser:
    payload = decode_token(token)
    subject = extract_token_subject(
        payload or {},
        expected_scope="admin",
        allow_unscoped=True,
    )
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    admin = db.get(AdminUser, int(subject))
    if not admin or admin.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account is unavailable",
        )

    return admin


def get_current_miniapp_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(miniapp_bearer),
) -> MiniappUser:
    token = credentials.credentials if credentials else ""
    payload = decode_token(token) if token else None
    subject = extract_token_subject(payload or {}, expected_scope="miniapp")
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Miniapp authentication required",
        )

    user = db.get(MiniappUser, int(subject))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Miniapp user is unavailable",
        )

    return user
