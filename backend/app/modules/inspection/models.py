"""巡检模块（消毒 / 安全检查）- ORM 模型。"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.assets.models import Asset
from app.modules.auth.models import User

TYPE_DISINFECT = "disinfect"  # 消毒
TYPE_SAFETY = "safety"        # 安全检查
INSPECTION_TYPES = [TYPE_DISINFECT, TYPE_SAFETY]

STATUS_PENDING = "pending"  # 待处理
STATUS_DONE = "done"        # 已完成

RESULT_PASS = "pass"  # 合格
RESULT_FAIL = "fail"  # 不合格


class InspectionTask(Base):
    __tablename__ = "inspection_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(20), default=TYPE_DISINFECT)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    # 数据域归属
    org_unit_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=STATUS_PENDING)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    asset: Mapped[Asset | None] = relationship(lazy="joined")
    assignee: Mapped[User | None] = relationship(lazy="joined", foreign_keys=[assignee_id])


class InspectionRecord(Base):
    __tablename__ = "inspection_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("inspection_tasks.id"))
    checker_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    result: Mapped[str] = mapped_column(String(20), default=RESULT_PASS)
    note: Mapped[str] = mapped_column(Text, default="")
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    checker: Mapped[User] = relationship(lazy="joined")
