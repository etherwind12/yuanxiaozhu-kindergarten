"""盘点模块 - ORM 模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.assets.models import Asset
from app.modules.auth.models import User

TASK_OPEN = "open"          # 盘点中
TASK_FINISHED = "finished"  # 已结束

RESULT_PENDING = "pending"  # 未盘
RESULT_MATCHED = "matched"  # 相符
RESULT_DIFF = "diff"        # 差异


class InventoryTask(Base):
    __tablename__ = "inventory_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    # 数据域归属（发起盘点的组织域）
    org_unit_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=TASK_OPEN)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    creator: Mapped[User] = relationship(lazy="joined")
    items: Mapped[list["InventoryItem"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", lazy="selectin"
    )


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("inventory_tasks.id"))
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    expected_qty: Mapped[int] = mapped_column(Integer, default=0)
    actual_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[str] = mapped_column(String(20), default=RESULT_PENDING)
    note: Mapped[str] = mapped_column(Text, default="")

    task: Mapped[InventoryTask] = relationship(back_populates="items")
    asset: Mapped[Asset] = relationship(lazy="joined")
