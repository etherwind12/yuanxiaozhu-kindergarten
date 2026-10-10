"""巡检模块 - 业务逻辑。"""

from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.scope import apply_org_scope, apply_owner_scope, ensure_org_scope, ensure_owner_scope
from app.modules.assets.models import Asset
from app.modules.inspection.models import (
    INSPECTION_TYPES,
    STATUS_DONE,
    STATUS_PENDING,
    InspectionRecord,
    InspectionTask,
)


def create_task(db: Session, data, user) -> InspectionTask:
    if data.type not in INSPECTION_TYPES:
        raise HTTPException(status_code=400, detail="巡检类型不合法（disinfect / safety）")
    org_unit_id = user.org_unit_id
    if data.asset_id is not None:
        asset = db.get(Asset, data.asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="资产不存在")
        ensure_org_scope(db, asset, user, "资产")
        org_unit_id = asset.org_unit_id or org_unit_id
    task = InspectionTask(
        title=data.title,
        type=data.type,
        asset_id=data.asset_id,
        org_unit_id=org_unit_id,
        assignee_id=data.assignee_id,
        created_by=user.id,
        due_date=data.due_date,
        note=data.note,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int, user=None) -> InspectionTask:
    task = db.get(InspectionTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="巡检任务不存在")
    if user is not None:
        ensure_org_scope(db, task, user, "巡检任务")
    return task


def complete_task(db: Session, task_id: int, user, result: str, note: str) -> InspectionTask:
    task = get_task(db, task_id, user)
    ensure_owner_scope(task, user, "created_by", "assignee_id", name="巡检任务")
    if task.status == STATUS_DONE:
        raise HTTPException(status_code=400, detail="该巡检任务已完成")
    record = InspectionRecord(task_id=task_id, checker_id=user.id, result=result, note=note)
    task.status = STATUS_DONE
    db.add(record)
    db.commit()
    db.refresh(task)
    return task


def list_tasks(db: Session, user, type_: str | None = None, status: str | None = None) -> list[InspectionTask]:
    stmt = apply_org_scope(select(InspectionTask), InspectionTask, db, user)
    stmt = apply_owner_scope(stmt, InspectionTask, user, "created_by", "assignee_id")
    if type_:
        stmt = stmt.where(InspectionTask.type == type_)
    if status:
        stmt = stmt.where(InspectionTask.status == status)
    return list(db.scalars(stmt.order_by(InspectionTask.id.desc())))


def list_records(db: Session, task_id: int, user) -> list[InspectionRecord]:
    task = get_task(db, task_id, user)
    ensure_owner_scope(task, user, "created_by", "assignee_id", name="巡检任务")
    return list(
        db.scalars(
            select(InspectionRecord)
            .where(InspectionRecord.task_id == task_id)
            .order_by(InspectionRecord.id.desc())
        )
    )


def generate_from_due(db: Session, user, within_days: int = 7) -> list[InspectionTask]:
    """根据资产的消毒 / 安全检查到期日，在当前数据域内自动生成待处理巡检任务。"""
    today = date.today()
    limit = today + timedelta(days=within_days)
    generated: list[InspectionTask] = []

    scoped_ids = apply_org_scope(select(InspectionTask), InspectionTask, db, user)
    existing = db.scalars(
        scoped_ids.where(InspectionTask.status == STATUS_PENDING)
    ).all()
    pending_keys = {(t.asset_id, t.type) for t in existing}

    stmt = apply_org_scope(select(Asset), Asset, db, user)
    for asset in db.scalars(stmt):
        for type_, due in (
            ("disinfect", asset.disinfect_due),
            ("safety", asset.safety_check_due),
        ):
            if due and due <= limit and (asset.id, type_) not in pending_keys:
                task = InspectionTask(
                    title=f"{asset.name} {'消毒' if type_ == 'disinfect' else '安全检查'}",
                    type=type_,
                    asset_id=asset.id,
                    org_unit_id=asset.org_unit_id or user.org_unit_id,
                    created_by=user.id,
                    due_date=due,
                )
                db.add(task)
                generated.append(task)
    db.commit()
    return generated
