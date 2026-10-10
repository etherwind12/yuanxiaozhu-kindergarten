"""教学联动模块 - 数据传输对象。"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.assets.schemas import AssetOut


class ReservationCreate(BaseModel):
    asset_id: int
    course_title: str = Field(min_length=1, max_length=100)
    use_date: date
    quantity: int = Field(default=1, ge=1)
    note: str = ""


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    asset_name: str = ""
    teacher_id: int
    teacher_name: str = ""
    course_title: str
    use_date: date
    quantity: int = 1
    status: str
    note: str
    created_at: datetime


def to_out(reservation) -> ReservationOut:
    return ReservationOut(
        id=reservation.id,
        asset_id=reservation.asset_id,
        asset_name=reservation.asset.name if reservation.asset else "",
        teacher_id=reservation.teacher_id,
        teacher_name=(reservation.teacher.full_name or reservation.teacher.username)
        if reservation.teacher
        else "",
        course_title=reservation.course_title,
        use_date=reservation.use_date,
        quantity=reservation.quantity,
        status=reservation.status,
        note=reservation.note,
        created_at=reservation.created_at,
    )


class AvailableAssetOut(AssetOut):
    """可预留教具：资产信息 + 当日已预留 / 剩余可预留数量。"""

    reserved_quantity: int = 0
    remaining_quantity: int = 0


def to_available_out(asset, reserved: int) -> AvailableAssetOut:
    return AvailableAssetOut(
        **AssetOut.model_validate(asset).model_dump(),
        reserved_quantity=reserved,
        remaining_quantity=asset.quantity - reserved,
    )
