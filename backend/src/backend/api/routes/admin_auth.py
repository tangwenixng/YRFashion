from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_admin
from backend.core.security import create_access_token, verify_password
from backend.db.session import get_db
from backend.models import AdminUser
from backend.schemas.auth import AdminLoginRequest, AdminProfileResponse, AdminTokenResponse

router = APIRouter(prefix="/admin/auth")


@router.post("/login", response_model=AdminTokenResponse)
def login(payload: AdminLoginRequest, db: Session = Depends(get_db)) -> AdminTokenResponse:
    admin = db.query(AdminUser).filter(AdminUser.username == payload.username).first()
    if admin is None or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if admin.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is disabled",
        )

    admin.last_login_at = datetime.now(UTC)
    db.add(admin)
    db.commit()

    return AdminTokenResponse(access_token=create_access_token(str(admin.id)))


@router.get("/me", response_model=AdminProfileResponse)
def me(current_admin: AdminUser = Depends(get_current_admin)) -> AdminProfileResponse:
    return AdminProfileResponse(
        id=current_admin.id,
        username=current_admin.username,
        display_name=current_admin.display_name,
    )
