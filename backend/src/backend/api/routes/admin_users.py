from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, MiniappUser
from backend.schemas.user import (
    MiniappUserAvatarReviewRequest,
    MiniappUserListResponse,
    MiniappUserResponse,
)

router = APIRouter(prefix="/admin/users")


def serialize_miniapp_user(user: MiniappUser) -> MiniappUserResponse:
    return MiniappUserResponse(
        id=user.id,
        openid=user.openid,
        unionid=user.unionid,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        pending_avatar_url=user.pending_avatar_url,
        avatar_review_status=user.avatar_review_status,
        avatar_reject_reason=user.avatar_reject_reason,
        first_visit_at=user.first_visit_at,
        last_visit_at=user.last_visit_at,
        created_at=user.created_at,
    )


@router.get("", response_model=MiniappUserListResponse)
def list_miniapp_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    keyword: str | None = Query(default=None, min_length=1, max_length=100),
    avatar_review_status: str | None = Query(default=None),
    sort: str = Query(default="last_visit_desc"),
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MiniappUserListResponse:
    query = db.query(MiniappUser)
    if keyword is not None and keyword.strip():
        normalized_keyword = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                MiniappUser.nickname.ilike(normalized_keyword),
                MiniappUser.openid.ilike(normalized_keyword),
                MiniappUser.unionid.ilike(normalized_keyword),
            )
        )

    normalized_review_status = (avatar_review_status or "").strip().lower()
    if normalized_review_status in {"pending", "approved", "rejected"}:
        query = query.filter(MiniappUser.avatar_review_status == normalized_review_status)

    if sort == "first_visit_desc":
        query = query.order_by(MiniappUser.first_visit_at.desc(), MiniappUser.id.desc())
    else:
        query = query.order_by(MiniappUser.last_visit_at.desc(), MiniappUser.id.desc())

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    return MiniappUserListResponse(
        items=[serialize_miniapp_user(user) for user in users],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("/{user_id}/avatar/approve", response_model=MiniappUserResponse)
def approve_user_avatar(
    user_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MiniappUserResponse:
    user = db.get(MiniappUser, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not (user.pending_avatar_url or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前用户没有待审核头像",
        )

    user.avatar_url = user.pending_avatar_url
    user.pending_avatar_url = None
    user.avatar_review_status = "approved"
    user.avatar_reject_reason = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_miniapp_user(user)


@router.post("/{user_id}/avatar/reject", response_model=MiniappUserResponse)
def reject_user_avatar(
    user_id: int,
    payload: MiniappUserAvatarReviewRequest,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
) -> MiniappUserResponse:
    user = db.get(MiniappUser, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not (user.pending_avatar_url or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前用户没有待审核头像",
        )

    reject_reason = payload.reason.strip() or "头像审核未通过，请重新上传清晰、合规的头像"
    user.pending_avatar_url = None
    user.avatar_review_status = "rejected"
    user.avatar_reject_reason = reject_reason
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_miniapp_user(user)
