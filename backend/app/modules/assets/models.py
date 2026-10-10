"""资产模块 - ORM 模型（分类 / 标签 / 资产）。"""

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# 资产与标签的多对多关联表
asset_tags = Table(
    "asset_tags",
    Base.metadata,
    Column("asset_id", ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

# 资产状态
STATUS_IN_STOCK = "in_stock"      # 在库
STATUS_BORROWED = "borrowed"      # 借出
STATUS_REPAIRING = "repairing"    # 维修中
STATUS_SCRAPPED = "scrapped"      # 已报废
STATUS_LOST = "lost"              # 遗失
ASSET_STATUSES = [STATUS_IN_STOCK, STATUS_BORROWED, STATUS_REPAIRING, STATUS_SCRAPPED, STATUS_LOST]

# 五大领域
DOMAINS = ["健康", "语言", "社会", "科学", "艺术"]

# 分类层级：资产大类 / 子类
KIND_MAJOR = "major"  # 资产大类
KIND_SUB = "sub"      # 子类

# 资产大类（玩具仅为其中一类）
MAJOR_CATEGORIES = [
    "玩具", "教具", "图书绘本", "教学设备", "电器家具",
    "体育器材", "办公用品", "生活用品", "消防安防", "其他",
]


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    # 树形分类：parent_id 为空表示顶层（资产大类）
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(20), default=KIND_MAJOR)
    description: Mapped[str] = mapped_column(String(255), default="")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    domain: Mapped[str] = mapped_column(String(20), default="")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # 二维码编号
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    # 数据域归属（园区/楼栋/班级）
    org_unit_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=STATUS_IN_STOCK)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit: Mapped[str] = mapped_column(String(20), default="件")  # 计量单位
    location: Mapped[str] = mapped_column(String(100), default="")  # 存放位置
    age_range: Mapped[str] = mapped_column(String(20), default="")  # 适龄段，如 3-4
    safety_level: Mapped[str] = mapped_column(String(20), default="")  # 安全等级
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    disinfect_due: Mapped[date | None] = mapped_column(Date, nullable=True)  # 消毒到期
    safety_check_due: Mapped[date | None] = mapped_column(Date, nullable=True)  # 安全检查到期
    remark: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    category: Mapped[Category | None] = relationship(lazy="joined")
    tags: Mapped[list[Tag]] = relationship(secondary=asset_tags, lazy="selectin")
