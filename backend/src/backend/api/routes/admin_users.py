from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.api.deps import get_current_admin
from backend.db.session import get_db
from backend.models import AdminUser, MiniappUser
from backend.schemas.user import MiniappUserListResponse, MiniappUserResponse

router = APIRouter(prefix="/admin/users")


@router.get("", response_model=MiniappUserListResponse)
def list_miniapp_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    keyword: str | None = Query(default=None, min_length=1, max_length=100),
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

    if sort == "first_visit_desc":
        query = query.order_by(MiniappUser.first_visit_at.desc(), MiniappUser.id.desc())
    else:
        query = query.order_by(MiniappUser.last_visit_at.desc(), MiniappUser.id.desc())

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    return MiniappUserListResponse(
        items=[
            MiniappUserResponse(
                id=user.id,
                openid=user.openid,
                unionid=user.unionid,
                nickname=user.nickname,
                avatar_url=user.avatar_url,
                first_visit_at=user.first_visit_at,
                last_visit_at=user.last_visit_at,
                created_at=user.created_at,
            )
            for user in users
        ],
        page=page,
        page_size=page_size,
        total=total,
    )
