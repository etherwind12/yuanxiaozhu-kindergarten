"""借还模块 - ORM 模型。"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.assets.models import Asset
from app.modules.auth.models import User

STATUS_BORROWING = "borrowing"  # 借用中
STATUS_RETURNED = "returned"    # 已归还


class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    borrower_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    # 数据域归属（取自资产，便于按域强制过滤）
    org_unit_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    borrow_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    due_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    return_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=STATUS_BORROWING)
    note: Mapped[str] = mapped_column(Text, default="")

    asset: Mapped[Asset] = relationship(lazy="joined")
    borrower: Mapped[User] = relationship(lazy="joined")
