"""认证与用户模块 - ORM 模型。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(50), default="")
    # admin(园长) / logistics(后勤) / teacher(教师) / caregiver(保育员)
    role: Mapped[str] = mapped_column(String(20), default="teacher")
    # 敏感字段：手机号经 AES 加密后落库
    phone: Mapped[str] = mapped_column(String(255), default="")
    # 数据域归属与数据范围（all / org / self）
    org_unit_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    data_scope: Mapped[str] = mapped_column(String(20), default="self")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
