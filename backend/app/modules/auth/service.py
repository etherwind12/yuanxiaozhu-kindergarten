"""认证与用户模块 - 业务逻辑。"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_field
from app.core.security import hash_password, verify_password
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate, UserUpdate
from app.modules.org.models import OrgUnit

VALID_ROLES = {"admin", "logistics", "teacher", "caregiver"}
VALID_SCOPES = {"all", "org", "self"}


def authenticate(db: Session, username: str, password: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被停用")
    return user


def _check_org_unit(db: Session, org_unit_id: int | None) -> None:
    if org_unit_id is not None and not db.get(OrgUnit, org_unit_id):
        raise HTTPException(status_code=400, detail="组织域不存在")


def create_user(db: Session, data: UserCreate) -> User:
    if db.scalar(select(User).where(User.username == data.username)):
        raise HTTPException(status_code=400, detail="用户名已存在")
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"角色不合法，可选：{sorted(VALID_ROLES)}")
    if data.data_scope not in VALID_SCOPES:
        raise HTTPException(status_code=400, detail=f"数据范围不合法，可选：{sorted(VALID_SCOPES)}")
    _check_org_unit(db, data.org_unit_id)
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        phone=encrypt_field(data.phone) or "",
        org_unit_id=data.org_unit_id,
        data_scope=data.data_scope,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    if data.role is not None:
        if data.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail="角色不合法")
        user.role = data.role
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.phone is not None:
        user.phone = encrypt_field(data.phone) or ""
    if data.org_unit_id is not None:
        _check_org_unit(db, data.org_unit_id)
        user.org_unit_id = data.org_unit_id
    if data.data_scope is not None:
        if data.data_scope not in VALID_SCOPES:
            raise HTTPException(status_code=400, detail="数据范围不合法")
        user.data_scope = data.data_scope
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))
