"""组织与数据域模块 - ORM 模型（组织树）。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# 组织域类型
TYPE_PARK = "park"          # 园区
TYPE_BUILDING = "building"  # 楼栋
TYPE_CLASS = "class"        # 班级
ORG_TYPES = [TYPE_PARK, TYPE_BUILDING, TYPE_CLASS]


class OrgUnit(Base):
    __tablename__ = "org_units"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(20), default=TYPE_PARK)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    children: Mapped[list["OrgUnit"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    parent: Mapped["OrgUnit | None"] = relationship(back_populates="children", remote_side="OrgUnit.id")
