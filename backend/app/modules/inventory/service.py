"""盘点模块 - 业务逻辑。"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.scope import apply_org_scope, apply_owner_scope, ensure_org_scope, ensure_owner_scope
from app.modules.assets.models import Asset
from app.modules.inventory.models import (
    RESULT_DIFF,
    RESULT_MATCHED,
    RESULT_PENDING,
    TASK_FINISHED,
    InventoryItem,
    InventoryTask,
)


def create_task(db: Session, title: str, user, note: str) -> InventoryTask:
    task = InventoryTask(
        title=title, created_by=user.id, org_unit_id=user.org_unit_id, note=note
    )
    db.add(task)
    db.flush()  # 拿到 task.id

    # 仅为当前数据域内的资产生成明细
    stmt = apply_org_scope(select(Asset), Asset, db, user)
    assets = list(db.scalars(stmt))
    for asset in assets:
        db.add(
            InventoryItem(task_id=task.id, asset_id=asset.id, expected_qty=asset.quantity)
        )
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int, user=None) -> InventoryTask:
    task = db.get(InventoryTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="盘点任务不存在")
    if user is not None:
        ensure_org_scope(db, task, user, "盘点任务")
    return task


def scan(
    db: Session, task_id: int, user, code: str | None, asset_id: int | None, actual_qty: int, note: str
) -> InventoryItem:
    task = get_task(db, task_id, user)
    ensure_owner_scope(task, user, "created_by", name="盘点任务")
    if task.status == TASK_FINISHED:
        raise HTTPException(status_code=400, detail="该盘点任务已结束")

    if asset_id is None:
        if not code:
            raise HTTPException(status_code=400, detail="请提供扫码编号或资产 ID")
        asset = db.scalar(select(Asset).where(Asset.code == code))
        if not asset:
            raise HTTPException(status_code=404, detail="未找到对应资产")
        asset_id = asset.id

    item = db.scalar(
        select(InventoryItem).where(
            InventoryItem.task_id == task_id, InventoryItem.asset_id == asset_id
        )
    )
    if not item:
        raise HTTPException(status_code=404, detail="该资产不在本次盘点范围内")

    item.actual_qty = actual_qty
    item.note = note
    item.result = RESULT_MATCHED if actual_qty == item.expected_qty else RESULT_DIFF
    db.commit()
    db.refresh(item)
    return item


def finish(db: Session, task_id: int, user) -> InventoryTask:
    task = get_task(db, task_id, user)
    ensure_owner_scope(task, user, "created_by", name="盘点任务")
    task.status = TASK_FINISHED
    # 未盘点的项目保留为 pending，便于后续追溯
    db.commit()
    db.refresh(task)
    return task


def list_tasks(db: Session, user) -> list[InventoryTask]:
    stmt = apply_org_scope(select(InventoryTask), InventoryTask, db, user)
    stmt = apply_owner_scope(stmt, InventoryTask, user, "created_by")
    return list(db.scalars(stmt.order_by(InventoryTask.id.desc())))


def list_items(db: Session, task_id: int, user) -> list[InventoryItem]:
    task = get_task(db, task_id, user)
    ensure_owner_scope(task, user, "created_by", name="盘点任务")
    return list(
        db.scalars(
            select(InventoryItem)
            .where(InventoryItem.task_id == task_id)
            .order_by(InventoryItem.id)
        )
    )
