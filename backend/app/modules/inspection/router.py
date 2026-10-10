"""巡检模块 - 路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.deps import ROLE_ADMIN, ROLE_CAREGIVER, ROLE_LOGISTICS, get_current_user, require_roles
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.inspection import service
from app.modules.inspection.schemas import CompleteIn, RecordOut, TaskCreate, TaskOut, record_to_out, task_to_out

router = APIRouter()

_operator = require_roles(ROLE_ADMIN, ROLE_LOGISTICS, ROLE_CAREGIVER)


@router.get("", response_model=list[TaskOut], summary="巡检任务列表")
def list_tasks(
    type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TaskOut]:
    return [task_to_out(t) for t in service.list_tasks(db, user, type_=type, status=status)]


@router.post("", response_model=TaskOut, summary="新建巡检任务")
def create_task(
    payload: TaskCreate, db: Session = Depends(get_db), user: User = Depends(_operator)
) -> TaskOut:
    return task_to_out(service.create_task(db, payload, user))


@router.post("/generate-from-due", response_model=list[TaskOut], summary="按到期日自动生成巡检任务")
def generate_from_due(
    within_days: int = Query(default=7, ge=0, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(_operator),
) -> list[TaskOut]:
    return [task_to_out(t) for t in service.generate_from_due(db, user, within_days)]


@router.get("/{task_id}/records", response_model=list[RecordOut], summary="巡检记录")
def list_records(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[RecordOut]:
    return [record_to_out(r) for r in service.list_records(db, task_id, user)]


@router.post("/{task_id}/complete", response_model=TaskOut, summary="完成巡检")
def complete(
    task_id: int,
    payload: CompleteIn,
    db: Session = Depends(get_db),
    user: User = Depends(_operator),
) -> TaskOut:
    return task_to_out(service.complete_task(db, task_id, user, payload.result, payload.note))
