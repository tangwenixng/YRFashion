from datetime import datetime

from pydantic import BaseModel


class MiniappUserResponse(BaseModel):
    id: int
    openid: str
    unionid: str | None
    nickname: str | None
    avatar_url: str | None
    first_visit_at: datetime
    last_visit_at: datetime
    created_at: datetime


class MiniappUserListResponse(BaseModel):
    items: list[MiniappUserResponse]
    page: int
    page_size: int
    total: int
