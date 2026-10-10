"""公共依赖：当前用户解析与角色权限校验。"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.modules.auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 角色常量
ROLE_ADMIN = "admin"          # 园长 / 系统管理员
ROLE_LOGISTICS = "logistics"  # 后勤 / 资产管理员
ROLE_TEACHER = "teacher"      # 教师
ROLE_CAREGIVER = "caregiver"  # 保育员


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise credentials_error

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise credentials_error
    return user


def require_roles(*roles: str):
    """生成一个校验指定角色的依赖。不传角色表示仅需登录。"""

    def checker(user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
        return user

    return checker
