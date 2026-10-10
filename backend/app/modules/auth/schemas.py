"""认证与用户模块 - 数据传输对象（Pydantic）。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.crypto import decrypt_field, mask_value


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = ""
    role: str = "teacher"
    phone: str = ""
    org_unit_id: int | None = None
    data_scope: str = "self"


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    phone: str | None = None
    org_unit_id: int | None = None
    data_scope: str | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str
    phone: str = ""
    org_unit_id: int | None = None
    data_scope: str = "self"
    is_active: bool
    created_at: datetime


def to_out(user, viewer=None) -> UserOut:
    """输出用户信息，手机号脱敏：仅本人可见全量，列表等场景一律脱敏（138****1234）。"""
    can_view_full = viewer is not None and viewer.id == user.id
    phone = decrypt_field(user.phone)
    return UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        phone=(phone or "") if can_view_full else mask_value(phone),
        org_unit_id=user.org_unit_id,
        data_scope=user.data_scope,
        is_active=user.is_active,
        created_at=user.created_at,
    )
