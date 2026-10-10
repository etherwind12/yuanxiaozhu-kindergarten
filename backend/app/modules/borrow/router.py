"""借还模块 - 路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.deps import ROLE_ADMIN, ROLE_CAREGIVER, ROLE_LOGISTICS, ROLE_TEACHER, get_current_user, require_roles
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.borrow import service
from app.modules.borrow.schemas import BorrowCreate, BorrowOut, to_out

router = APIRouter()

# 教师、保育员、后勤、园长均可借用
_operator = require_roles(ROLE_ADMIN, ROLE_LOGISTICS, ROLE_TEACHER, ROLE_CAREGIVER)


@router.get("", response_model=list[BorrowOut], summary="借还记录列表")
def list_records(
    status: str | None = Query(default=None),
    asset_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[BorrowOut]:
    return [to_out(r) for r in service.list_records(db, user, status=status, asset_id=asset_id)]


@router.post("", response_model=BorrowOut, summary="借出资产")
def borrow(
    payload: BorrowCreate,
    db: Session = Depends(get_db),
    user: User = Depends(_operator),
) -> BorrowOut:
    record = service.borrow_asset(db, payload.asset_id, user, payload.due_at, payload.note)
    return to_out(record)


@router.post("/{record_id}/return", response_model=BorrowOut, summary="归还资产")
def return_asset(
    record_id: int, db: Session = Depends(get_db), user: User = Depends(_operator)
) -> BorrowOut:
    return to_out(service.return_asset(db, record_id, user))
