"""盘点模块 - 路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.deps import ROLE_ADMIN, ROLE_CAREGIVER, ROLE_LOGISTICS, get_current_user, require_roles
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.inventory import service
from app.modules.inventory.schemas import ItemOut, ScanIn, TaskCreate, TaskOut, item_to_out, task_to_out

router = APIRouter()

_writer = require_roles(ROLE_ADMIN, ROLE_LOGISTICS, ROLE_CAREGIVER)


@router.get("", response_model=list[TaskOut], summary="盘点任务列表")
def list_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[TaskOut]:
    return [task_to_out(t) for t in service.list_tasks(db, user)]


@router.post("", response_model=TaskOut, summary="发起盘点任务")
def create_task(
    payload: TaskCreate, db: Session = Depends(get_db), user: User = Depends(_writer)
) -> TaskOut:
    return task_to_out(service.create_task(db, payload.title, user, payload.note))


@router.get("/{task_id}", response_model=TaskOut, summary="盘点任务详情")
def get_task(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> TaskOut:
    return task_to_out(service.get_task(db, task_id, user))


@router.get("/{task_id}/items", response_model=list[ItemOut], summary="盘点明细")
def list_items(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[ItemOut]:
    return [item_to_out(i) for i in service.list_items(db, task_id, user)]


@router.post("/{task_id}/scan", response_model=ItemOut, summary="扫码/登记盘点结果")
def scan(
    task_id: int, payload: ScanIn, db: Session = Depends(get_db), user: User = Depends(_writer)
) -> ItemOut:
    item = service.scan(db, task_id, user, payload.code, payload.asset_id, payload.actual_qty, payload.note)
    return item_to_out(item)


@router.post("/{task_id}/finish", response_model=TaskOut, summary="结束盘点")
def finish(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(_writer)
) -> TaskOut:
    return task_to_out(service.finish(db, task_id, user))
