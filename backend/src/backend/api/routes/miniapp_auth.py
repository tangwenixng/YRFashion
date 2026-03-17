from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend.api.deps import get_current_miniapp_user
from backend.core.security import create_access_token
from backend.db.session import get_db
from backend.models import MiniappUser
from backend.schemas.miniapp import (
    MiniappAvatarUploadResponse,
    MiniappLoginRequest,
    MiniappLoginResponse,
    MiniappProfileResponse,
    MiniappProfileUpdateRequest,
)
from backend.services.content_safety import ensure_safe_text
from backend.services.miniapp_auth import resolve_openid_from_code
from backend.services.storage import save_miniapp_avatar

router = APIRouter(prefix="/miniapp/auth")


def serialize_miniapp_profile(user: MiniappUser) -> MiniappProfileResponse:
    return MiniappProfileResponse(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        pending_avatar_url=user.pending_avatar_url,
        avatar_review_status=user.avatar_review_status,
        avatar_reject_reason=user.avatar_reject_reason,
        created_at=user.created_at,
        last_visit_at=user.last_visit_at,
    )


@router.post("/login", response_model=MiniappLoginResponse)
def login(payload: MiniappLoginRequest, db: Session = Depends(get_db)) -> MiniappLoginResponse:
    openid = resolve_openid_from_code(payload.code)
    now = datetime.now(UTC)
    user = db.query(MiniappUser).filter(MiniappUser.openid == openid).first()

    if user is None:
        user = MiniappUser(
            openid=openid,
            unionid=None,
            nickname=None,
            avatar_url=None,
            first_visit_at=now,
            last_visit_at=now,
        )
        db.add(user)
    else:
        user.last_visit_at = now
        db.add(user)

    db.commit()
    db.refresh(user)

    return MiniappLoginResponse(
        access_token=create_access_token(str(user.id), scope="miniapp"),
        user=serialize_miniapp_profile(user),
    )


@router.put("/profile", response_model=MiniappProfileResponse)
def update_profile(
    payload: MiniappProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: MiniappUser = Depends(get_current_miniapp_user),
) -> MiniappProfileResponse:
    current_user.nickname = ensure_safe_text(payload.nickname, field_label="昵称")
    normalized_avatar_url = payload.avatar_url.strip()
    if normalized_avatar_url == (current_user.pending_avatar_url or "").strip():
        current_user.avatar_review_status = "pending"
        current_user.avatar_reject_reason = None
    elif normalized_avatar_url == (current_user.avatar_url or "").strip():
        current_user.pending_avatar_url = None
        current_user.avatar_review_status = "approved"
        current_user.avatar_reject_reason = None
    else:
        current_user.pending_avatar_url = normalized_avatar_url
        current_user.avatar_review_status = "pending"
        current_user.avatar_reject_reason = None

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return serialize_miniapp_profile(current_user)


@router.post("/avatar", response_model=MiniappAvatarUploadResponse)
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: MiniappUser = Depends(get_current_miniapp_user),
) -> MiniappAvatarUploadResponse:
    _, avatar_url = save_miniapp_avatar(current_user.id, file)
    current_user.pending_avatar_url = avatar_url
    current_user.avatar_review_status = "pending"
    current_user.avatar_reject_reason = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return MiniappAvatarUploadResponse(
        avatar_url=avatar_url,
        pending_avatar_url=current_user.pending_avatar_url,
        avatar_review_status=current_user.avatar_review_status,
        avatar_reject_reason=current_user.avatar_reject_reason,
    )
