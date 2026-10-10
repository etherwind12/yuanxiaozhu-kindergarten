"""教学联动模块 - 业务逻辑。

把「资产」与「教学」打通：教师可按主题/领域检索可用教具并预留。
预留按「数量」占用：同一教具同一天，累计预留数量不得超过资产总量。
"""

from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.scope import apply_org_scope, apply_owner_scope, ensure_org_scope
from app.modules.assets.models import STATUS_IN_STOCK, Asset, Tag
from app.modules.teaching.models import (
    RESERVATION_STATUSES,
    STATUS_APPROVED,
    STATUS_FINISHED,
    STATUS_PENDING,
    STATUS_REJECTED,
    Reservation,
)

# 占用档期的状态
_ACTIVE_STATUSES = [STATUS_PENDING, STATUS_APPROVED]


def reserved_quantity(db: Session, asset_id: int, use_date: date, exclude_id: int | None = None) -> int:
    """某教具在某日、占用状态下的已预留总数量。"""
    stmt = select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
        Reservation.asset_id == asset_id,
        Reservation.use_date == use_date,
        Reservation.status.in_(_ACTIVE_STATUSES),
    )
    if exclude_id is not None:
        stmt = stmt.where(Reservation.id != exclude_id)
    return int(db.scalar(stmt) or 0)


def create_reservation(db: Session, user, data) -> Reservation:
    asset = db.get(Asset, data.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    ensure_org_scope(db, asset, user, "资产")

    unit = asset.unit or "件"
    reserved = reserved_quantity(db, data.asset_id, data.use_date)
    remaining = asset.quantity - reserved
    if remaining <= 0:
        raise HTTPException(status_code=400, detail=f"该教具当日已全部预留（共 {asset.quantity} {unit}）")
    if data.quantity > remaining:
        raise HTTPException(
            status_code=400,
            detail=f"当日最多还可预留 {remaining} {unit}（共 {asset.quantity} {unit}，已预留 {reserved} {unit}）",
        )

    reservation = Reservation(
        asset_id=data.asset_id,
        teacher_id=user.id,
        org_unit_id=asset.org_unit_id or user.org_unit_id,
        course_title=data.course_title,
        use_date=data.use_date,
        quantity=data.quantity,
        note=data.note,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def get_reservation(db: Session, reservation_id: int, user=None) -> Reservation:
    reservation = db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="预留记录不存在")
    if user is not None:
        ensure_org_scope(db, reservation, user, "预留记录")
    return reservation


def change_status(db: Session, reservation_id: int, status: str, user=None) -> Reservation:
    if status not in RESERVATION_STATUSES:
        raise HTTPException(status_code=400, detail="状态不合法")
    reservation = get_reservation(db, reservation_id, user)
    reservation.status = status
    db.commit()
    db.refresh(reservation)
    return reservation


def list_reservations(
    db: Session,
    user,
    teacher_id: int | None = None,
    status: str | None = None,
    use_date: date | None = None,
) -> list[Reservation]:
    stmt = select(Reservation)
    stmt = apply_org_scope(stmt, Reservation, db, user)
    stmt = apply_owner_scope(stmt, Reservation, user, "teacher_id")
    if teacher_id:
        stmt = stmt.where(Reservation.teacher_id == teacher_id)
    if status:
        stmt = stmt.where(Reservation.status == status)
    if use_date:
        stmt = stmt.where(Reservation.use_date == use_date)
    return list(db.scalars(stmt.order_by(Reservation.id.desc())))


def available_assets(
    db: Session, user, use_date: date | None = None, domain: str | None = None, keyword: str | None = None
) -> list[tuple[Asset, int]]:
    """可预留教具：本数据域内、在库，且当日仍有剩余可预留数量。

    返回 (资产, 当日已预留数量) 列表。
    """
    stmt = select(Asset).where(Asset.status == STATUS_IN_STOCK)
    stmt = apply_org_scope(stmt, Asset, db, user)
    if domain:
        stmt = stmt.where(Asset.tags.any(Tag.domain == domain))
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(Asset.name.like(like))
    assets = list(db.scalars(stmt.order_by(Asset.id.desc())))
    if not assets:
        return []

    reserved_map: dict[int, int] = {}
    if use_date:
        rows = db.execute(
            select(Reservation.asset_id, func.coalesce(func.sum(Reservation.quantity), 0))
            .where(
                Reservation.use_date == use_date,
                Reservation.status.in_(_ACTIVE_STATUSES),
                Reservation.asset_id.in_([a.id for a in assets]),
            )
            .group_by(Reservation.asset_id)
        ).all()
        reserved_map = {asset_id: int(qty or 0) for asset_id, qty in rows}

    return [
        (a, reserved_map.get(a.id, 0))
        for a in assets
        if a.quantity - reserved_map.get(a.id, 0) > 0
    ]
