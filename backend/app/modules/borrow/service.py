"""借还模块 - 业务逻辑。"""

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.scope import apply_org_scope, apply_owner_scope, ensure_org_scope, ensure_owner_scope
from app.modules.assets.models import STATUS_BORROWED, STATUS_IN_STOCK, Asset
from app.modules.borrow.models import STATUS_BORROWING, STATUS_RETURNED, BorrowRecord


def borrow_asset(db: Session, asset_id: int, user, due_at, note: str) -> BorrowRecord:
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    ensure_org_scope(db, asset, user, "资产")
    if asset.status != STATUS_IN_STOCK:
        raise HTTPException(status_code=400, detail="该资产当前不可借出")
    record = BorrowRecord(
        asset_id=asset_id,
        borrower_id=user.id,
        org_unit_id=asset.org_unit_id or user.org_unit_id,
        due_at=due_at,
        note=note,
    )
    asset.status = STATUS_BORROWED
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def return_asset(db: Session, record_id: int, user) -> BorrowRecord:
    record = db.get(BorrowRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="借还记录不存在")
    ensure_org_scope(db, record, user, "借还记录")
    ensure_owner_scope(record, user, "borrower_id", name="借还记录")
    if record.status != STATUS_BORROWING:
        raise HTTPException(status_code=400, detail="该记录已归还")
    record.status = STATUS_RETURNED
    record.return_at = datetime.utcnow()
    if record.asset:
        record.asset.status = STATUS_IN_STOCK
    db.commit()
    db.refresh(record)
    return record


def list_records(
    db: Session, user, status: str | None = None, asset_id: int | None = None
) -> list[BorrowRecord]:
    stmt = select(BorrowRecord)
    stmt = apply_org_scope(stmt, BorrowRecord, db, user)
    stmt = apply_owner_scope(stmt, BorrowRecord, user, "borrower_id")
    if status:
        stmt = stmt.where(BorrowRecord.status == status)
    if asset_id:
        stmt = stmt.where(BorrowRecord.asset_id == asset_id)
    return list(db.scalars(stmt.order_by(BorrowRecord.id.desc())))
