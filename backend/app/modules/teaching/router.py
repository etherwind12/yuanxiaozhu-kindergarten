"""教学联动模块 - 路由。"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.deps import ROLE_ADMIN, ROLE_LOGISTICS, ROLE_TEACHER, get_current_user, require_roles
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.teaching import service
from app.modules.teaching.schemas import (
    AvailableAssetOut,
    ReservationCreate,
    ReservationOut,
    to_available_out,
    to_out,
)

router = APIRouter()

_approver = require_roles(ROLE_ADMIN, ROLE_LOGISTICS)
_teacher = require_roles(ROLE_ADMIN, ROLE_LOGISTICS, ROLE_TEACHER)


@router.get("/available", response_model=list[AvailableAssetOut], summary="可预留教具（按领域/日期/关键字）")
def available(
    use_date: date | None = Query(default=None),
    domain: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return [
        to_available_out(asset, reserved)
        for asset, reserved in service.available_assets(
            db, user, use_date=use_date, domain=domain, keyword=keyword
        )
    ]


@router.get("", response_model=list[ReservationOut], summary="预留列表")
def list_reservations(
    teacher_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    use_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ReservationOut]:
    return [to_out(r) for r in service.list_reservations(db, user, teacher_id, status, use_date)]


@router.post("", response_model=ReservationOut, summary="发起教具预留")
def create_reservation(
    payload: ReservationCreate, db: Session = Depends(get_db), user: User = Depends(_teacher)
) -> ReservationOut:
    return to_out(service.create_reservation(db, user, payload))


@router.post("/{reservation_id}/approve", response_model=ReservationOut, summary="通过预留")
def approve(
    reservation_id: int, db: Session = Depends(get_db), user: User = Depends(_approver)
) -> ReservationOut:
    return to_out(service.change_status(db, reservation_id, "approved", user))


@router.post("/{reservation_id}/reject", response_model=ReservationOut, summary="驳回预留")
def reject(
    reservation_id: int, db: Session = Depends(get_db), user: User = Depends(_approver)
) -> ReservationOut:
    return to_out(service.change_status(db, reservation_id, "rejected", user))


@router.post("/{reservation_id}/finish", response_model=ReservationOut, summary="结束预留")
def finish(
    reservation_id: int, db: Session = Depends(get_db), user: User = Depends(_approver)
) -> ReservationOut:
    return to_out(service.change_status(db, reservation_id, "finished", user))
