"""巡检模块 - 数据传输对象。"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.meta import service as meta_service


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    type: str = "disinfect"
    asset_id: int | None = None
    assignee_id: int | None = None
    due_date: date | None = None
    note: str = ""


class CompleteIn(BaseModel):
    result: str = "pass"  # pass / fail
    note: str = ""


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    type: str
    type_text: str = ""
    type_tone: str = "default"
    asset_id: int | None
    asset_name: str = ""
    assignee_id: int | None
    assignee_name: str = ""
    due_date: date | None
    status: str
    status_text: str = ""
    status_tone: str = "default"
    overdue: bool = False
    note: str
    created_at: datetime


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    result: str
    result_text: str = ""
    result_tone: str = "default"
    note: str
    checked_at: datetime
    checker_name: str = ""


def task_to_out(task) -> TaskOut:
    overdue = bool(
        task.status == "pending" and task.due_date is not None and task.due_date < date.today()
    )
    return TaskOut(
        id=task.id,
        title=task.title,
        type=task.type,
        type_text=meta_service.inspection_type_text(task.type),
        type_tone=meta_service.inspection_type_tone(task.type),
        asset_id=task.asset_id,
        asset_name=task.asset.name if task.asset else "",
        assignee_id=task.assignee_id,
        assignee_name=(task.assignee.full_name or task.assignee.username) if task.assignee else "",
        due_date=task.due_date,
        status=task.status,
        status_text=meta_service.inspection_status_text(task.status, overdue),
        status_tone=meta_service.inspection_status_tone(task.status, overdue),
        overdue=overdue,
        note=task.note,
        created_at=task.created_at,
    )


def record_to_out(record) -> RecordOut:
    return RecordOut(
        id=record.id,
        task_id=record.task_id,
        result=record.result,
        result_text=meta_service.inspection_result_text(record.result),
        result_tone=meta_service.inspection_result_tone(record.result),
        note=record.note,
        checked_at=record.checked_at,
        checker_name=(record.checker.full_name or record.checker.username) if record.checker else "",
    )
