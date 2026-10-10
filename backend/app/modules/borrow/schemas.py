"""借还模块 - 数据传输对象。"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.modules.meta import service as meta_service


class BorrowCreate(BaseModel):
    asset_id: int
    due_at: date | None = None
    note: str = ""


class BorrowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    asset_name: str = ""
    borrower_id: int
    borrower_name: str = ""
    borrow_at: datetime
    due_at: date | None
    return_at: datetime | None
    status: str
    status_text: str = ""
    status_tone: str = "default"
    overdue: bool = False
    note: str


def to_out(record) -> BorrowOut:
    """把 ORM 记录转换为输出对象，附带冗余展示字段与逾期标记。"""
    overdue = bool(
        record.status == "borrowing" and record.due_at is not None and record.due_at < date.today()
    )
    return BorrowOut(
        id=record.id,
        asset_id=record.asset_id,
        asset_name=record.asset.name if record.asset else "",
        borrower_id=record.borrower_id,
        borrower_name=(record.borrower.full_name or record.borrower.username) if record.borrower else "",
        borrow_at=record.borrow_at,
        due_at=record.due_at,
        return_at=record.return_at,
        status=record.status,
        status_text=meta_service.borrow_status_text(record.status, overdue),
        status_tone=meta_service.borrow_status_tone(record.status, overdue),
        overdue=overdue,
        note=record.note,
    )
