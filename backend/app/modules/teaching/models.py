"""教学联动模块 - ORM 模型（教具预留）。"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.assets.models import Asset
from app.modules.auth.models import User

STATUS_PENDING = "pending"    # 待审批
STATUS_APPROVED = "approved"  # 已通过
STATUS_REJECTED = "rejected"  # 已驳回
STATUS_FINISHED = "finished"  # 已结束
RESERVATION_STATUSES = [STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED, STATUS_FINISHED]


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    # 数据域归属
    org_unit_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    course_title: Mapped[str] = mapped_column(String(100))  # 用途 / 主题 / 课程
    use_date: Mapped[date] = mapped_column(Date)            # 使用日期
    quantity: Mapped[int] = mapped_column(Integer, default=1)  # 本次预留数量
    status: Mapped[str] = mapped_column(String(20), default=STATUS_PENDING)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    asset: Mapped[Asset] = relationship(lazy="joined")
    teacher: Mapped[User] = relationship(lazy="joined")
