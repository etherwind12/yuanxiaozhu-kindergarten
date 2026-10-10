"""报表模块 - ORM 模型（导出溯源日志）。"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExportLog(Base):
    """导出记录：一次导出 = 一条可追溯记录（含暗水印码）。"""

    __tablename__ = "export_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(50), default="")
    full_name: Mapped[str] = mapped_column(String(50), default="")
    kind: Mapped[str] = mapped_column(String(30), default="report")
    scope: Mapped[str] = mapped_column(String(20), default="")
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    watermark: Mapped[str] = mapped_column(String(64), default="", index=True)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
