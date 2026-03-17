from datetime import datetime

from pydantic import BaseModel, Field


class MiniappUserAvatarReviewRequest(BaseModel):
    reason: str = Field(default="", max_length=255)


class MiniappUserResponse(BaseModel):
    id: int
    openid: str
    unionid: str | None
    nickname: str | None
    avatar_url: str | None
    pending_avatar_url: str | None
    avatar_review_status: str
    avatar_reject_reason: str | None
    first_visit_at: datetime
    last_visit_at: datetime
    created_at: datetime


class MiniappUserListResponse(BaseModel):
    items: list[MiniappUserResponse]
    page: int
    page_size: int
    total: int
