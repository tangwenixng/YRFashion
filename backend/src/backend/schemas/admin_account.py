from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AdminAccountStatus = Literal["active", "disabled"]


class AdminAccountResponse(BaseModel):
    id: int
    username: str
    display_name: str
    status: str
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AdminAccountListResponse(BaseModel):
    items: list[AdminAccountResponse]


class AdminAccountCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    status: AdminAccountStatus = "active"


class AdminAccountUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    status: AdminAccountStatus | None = None


class AdminAccountResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)
