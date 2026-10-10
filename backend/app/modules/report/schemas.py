"""报表模块 - 数据传输对象。"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class NameCount(BaseModel):
    name: str
    count: int


class DueItem(BaseModel):
    asset_id: int
    asset_name: str
    type: str          # disinfect / safety
    due_date: date
    days_left: int     # 负数表示已逾期


class OverviewOut(BaseModel):
    asset_total: int
    status_counts: dict[str, int]
    by_category: list[NameCount]
    by_domain: list[NameCount]
    borrowing_count: int
    overdue_borrow_count: int
    inspection_pending: int
    inspection_overdue: int
    inventory_open: int
    due_soon: list[DueItem]


class WatermarkTraceIn(BaseModel):
    code: str


class WatermarkTraceOut(BaseModel):
    valid: bool
    username: str = ""
    full_name: str = ""
    exported_at: str = ""
    scope: str = ""
    row_count: int = 0
    message: str = ""


class ExportLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    kind: str
    scope: str
    row_count: int
    watermark: str
    created_at: datetime
