"""报表模块 - 业务逻辑（跨模块聚合，只读，按数据域过滤）。"""

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.scope import apply_org_scope, apply_owner_scope
from app.modules.assets.models import DOMAINS, KIND_MAJOR, KIND_SUB, Asset, Category, Tag
from app.modules.borrow.models import STATUS_BORROWING, BorrowRecord
from app.modules.inspection.models import STATUS_PENDING, InspectionTask
from app.modules.inventory.models import TASK_OPEN, InventoryTask
from app.modules.report.schemas import DueItem, NameCount, OverviewOut


def _status_counts(db: Session, user) -> dict[str, int]:
    stmt = apply_org_scope(select(Asset.status, func.count(Asset.id)), Asset, db, user)
    rows = db.execute(stmt.group_by(Asset.status)).all()
    return {status: count for status, count in rows}


def _by_category(db: Session, user) -> list[NameCount]:
    """按资产大类汇总（子类归并到大类；无资产的大类也返回 0）。"""
    majors = list(
        db.scalars(select(Category).where(Category.kind == KIND_MAJOR).order_by(Category.id))
    )
    parent_of = dict(
        db.execute(select(Category.id, Category.parent_id).where(Category.kind == KIND_SUB)).all()
    )
    counts = {major.id: 0 for major in majors}
    stmt = apply_org_scope(select(Asset.category_id), Asset, db, user)
    for category_id in db.scalars(stmt):
        if category_id is None:
            continue
        major_id = category_id if category_id in counts else parent_of.get(category_id)
        if major_id in counts:
            counts[major_id] += 1
    return [NameCount(name=major.name, count=counts[major.id]) for major in majors]


def _by_domain(db: Session, user) -> list[NameCount]:
    result: list[NameCount] = []
    for domain in DOMAINS:
        stmt = apply_org_scope(
            select(func.count(Asset.id)).where(Asset.tags.any(Tag.domain == domain)), Asset, db, user
        )
        count = db.scalar(stmt) or 0
        result.append(NameCount(name=domain, count=count))
    return result


def _due_soon(db: Session, user, within_days: int) -> list[DueItem]:
    limit = date.today() + timedelta(days=within_days)
    items: list[DueItem] = []
    for asset in db.scalars(apply_org_scope(select(Asset), Asset, db, user)):
        for type_, due in (("disinfect", asset.disinfect_due), ("safety", asset.safety_check_due)):
            if due and due <= limit:
                items.append(
                    DueItem(
                        asset_id=asset.id,
                        asset_name=asset.name,
                        type=type_,
                        due_date=due,
                        days_left=(due - date.today()).days,
                    )
                )
    items.sort(key=lambda i: i.days_left)
    return items


def _count(db: Session, stmt, model, user, owner_field: str | None = None) -> int:
    stmt = apply_org_scope(stmt, model, db, user)
    if owner_field:
        stmt = apply_owner_scope(stmt, model, user, owner_field)
    return db.scalar(stmt) or 0


def overview(db: Session, user, within_days: int = 7) -> OverviewOut:
    counts = _status_counts(db, user)
    total = sum(counts.values())

    borrowing_count = _count(
        db,
        select(func.count(BorrowRecord.id)).where(BorrowRecord.status == STATUS_BORROWING),
        BorrowRecord, user, "borrower_id",
    )
    overdue_borrow_count = _count(
        db,
        select(func.count(BorrowRecord.id)).where(
            BorrowRecord.status == STATUS_BORROWING,
            BorrowRecord.due_at.is_not(None),
            BorrowRecord.due_at < date.today(),
        ),
        BorrowRecord, user, "borrower_id",
    )

    inspection_pending = _count(
        db,
        select(func.count(InspectionTask.id)).where(InspectionTask.status == STATUS_PENDING),
        InspectionTask, user,
    )
    inspection_overdue = _count(
        db,
        select(func.count(InspectionTask.id)).where(
            InspectionTask.status == STATUS_PENDING,
            InspectionTask.due_date.is_not(None),
            InspectionTask.due_date < date.today(),
        ),
        InspectionTask, user,
    )

    inventory_open = _count(
        db,
        select(func.count(InventoryTask.id)).where(InventoryTask.status == TASK_OPEN),
        InventoryTask, user,
    )

    return OverviewOut(
        asset_total=total,
        status_counts=counts,
        by_category=_by_category(db, user),
        by_domain=_by_domain(db, user),
        borrowing_count=borrowing_count,
        overdue_borrow_count=overdue_borrow_count,
        inspection_pending=inspection_pending,
        inspection_overdue=inspection_overdue,
        inventory_open=inventory_open,
        due_soon=_due_soon(db, user, within_days),
    )
