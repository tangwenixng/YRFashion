from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.core.security import decode_token
from backend.db.session import get_db
from backend.models import AdminUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/auth/login")


def get_current_admin(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> AdminUser:
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    admin = db.get(AdminUser, int(payload["sub"]))
    if not admin or admin.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account is unavailable",
        )

    return admin
