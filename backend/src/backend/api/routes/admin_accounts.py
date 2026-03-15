from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.deps import get_current_admin
from backend.core.security import get_password_hash
from backend.db.session import get_db
from backend.models import AdminUser
from backend.schemas.admin_account import (
    AdminAccountCreateRequest,
    AdminAccountListResponse,
    AdminAccountResetPasswordRequest,
    AdminAccountResponse,
    AdminAccountUpdateRequest,
)

router = APIRouter(prefix="/admin/accounts")


def serialize_admin(admin: AdminUser) -> AdminAccountResponse:
    return AdminAccountResponse(
        id=admin.id,
        username=admin.username,
        display_name=admin.display_name,
        status=admin.status,
        last_login_at=admin.last_login_at,
        created_at=admin.created_at,
        updated_at=admin.updated_at,
    )


def load_admin_or_404(db: Session, admin_id: int) -> AdminUser:
    admin = db.get(AdminUser, admin_id)
    if admin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin account not found")
    return admin


def ensure_username_available(db: Session, username: str, exclude_admin_id: int | None = None) -> None:
    query = db.query(AdminUser).filter(AdminUser.username == username)
    if exclude_admin_id is not None:
        query = query.filter(AdminUser.id != exclude_admin_id)
    if query.first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin username exists")


@router.get("", response_model=AdminAccountListResponse)
def list_admin_accounts(
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminAccountListResponse:
    admins = db.query(AdminUser).order_by(AdminUser.created_at.asc(), AdminUser.id.asc()).all()
    return AdminAccountListResponse(items=[serialize_admin(admin) for admin in admins])


@router.post("", response_model=AdminAccountResponse, status_code=status.HTTP_201_CREATED)
def create_admin_account(
    payload: AdminAccountCreateRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminAccountResponse:
    username = payload.username.strip()
    ensure_username_available(db, username)

    admin = AdminUser(
        username=username,
        display_name=payload.display_name.strip(),
        password_hash=get_password_hash(payload.password),
        status=payload.status,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return serialize_admin(admin)


@router.patch("/{admin_id}", response_model=AdminAccountResponse)
def update_admin_account(
    admin_id: int,
    payload: AdminAccountUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> AdminAccountResponse:
    admin = load_admin_or_404(db, admin_id)

    if payload.display_name is not None:
        admin.display_name = payload.display_name.strip()
    if payload.status is not None:
        if current_admin.id == admin.id and payload.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current admin cannot disable own account",
            )
        admin.status = payload.status

    db.add(admin)
    db.commit()
    db.refresh(admin)
    return serialize_admin(admin)


@router.post("/{admin_id}/reset-password", response_model=AdminAccountResponse)
def reset_admin_password(
    admin_id: int,
    payload: AdminAccountResetPasswordRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> AdminAccountResponse:
    admin = load_admin_or_404(db, admin_id)
    admin.password_hash = get_password_hash(payload.new_password)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return serialize_admin(admin)
