from datetime import datetime

from pydantic import BaseModel, Field


class MiniappLoginRequest(BaseModel):
    code: str = Field(min_length=1, max_length=256)


class MiniappProfileResponse(BaseModel):
    id: int
    created_at: datetime
    last_visit_at: datetime


class MiniappLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: MiniappProfileResponse
