"""认证与用户模块 - 路由。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.deps import ROLE_ADMIN, get_current_user, require_roles
from app.core.database import get_db
from app.core.security import create_access_token
from app.modules.auth import service
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, Token, UserCreate, UserOut, UserUpdate, to_out

router = APIRouter()


@router.post("/login", response_model=Token, summary="登录获取令牌")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = service.authenticate(db, payload.username, payload.password)
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut, summary="获取当前登录用户")
def me(user: User = Depends(get_current_user)) -> UserOut:
    return to_out(user, viewer=user)


@router.get("/users", response_model=list[UserOut], summary="用户列表")
def list_users(
    db: Session = Depends(get_db),
    viewer: User = Depends(require_roles(ROLE_ADMIN)),
) -> list[UserOut]:
    return [to_out(u, viewer=viewer) for u in service.list_users(db)]


@router.post("/users", response_model=UserOut, summary="新建用户")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    viewer: User = Depends(require_roles(ROLE_ADMIN)),
) -> UserOut:
    return to_out(service.create_user(db, payload), viewer=viewer)


@router.patch("/users/{user_id}", response_model=UserOut, summary="更新用户")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    viewer: User = Depends(require_roles(ROLE_ADMIN)),
) -> UserOut:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return to_out(service.update_user(db, user, payload), viewer=viewer)
