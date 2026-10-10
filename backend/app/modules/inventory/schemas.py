"""盘点模块 - 数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    note: str = ""


class ScanIn(BaseModel):
    code: str | None = None       # 扫码编号
    asset_id: int | None = None   # 或直接指定资产
    actual_qty: int = 0
    note: str = ""


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    asset_name: str = ""
    asset_code: str = ""
    expected_qty: int
    actual_qty: int | None
    result: str
    note: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: str
    note: str
    created_at: datetime
    created_by_name: str = ""
    total: int = 0
    checked: int = 0
    diff_count: int = 0


def item_to_out(item) -> ItemOut:
    return ItemOut(
        id=item.id,
        asset_id=item.asset_id,
        asset_name=item.asset.name if item.asset else "",
        asset_code=item.asset.code if item.asset else "",
        expected_qty=item.expected_qty,
        actual_qty=item.actual_qty,
        result=item.result,
        note=item.note,
    )


def task_to_out(task) -> TaskOut:
    items = task.items or []
    return TaskOut(
        id=task.id,
        title=task.title,
        status=task.status,
        note=task.note,
        created_at=task.created_at,
        created_by_name=(task.creator.full_name or task.creator.username) if task.creator else "",
        total=len(items),
        checked=sum(1 for i in items if i.result != "pending"),
        diff_count=sum(1 for i in items if i.result == "diff"),
    )
