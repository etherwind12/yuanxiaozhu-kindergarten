"""报表模块 - 路由。"""

from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.deps import ROLE_ADMIN, ROLE_LOGISTICS, get_current_user, require_roles
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.report import export, service
from app.modules.report.models import ExportLog
from app.modules.report.schemas import (
    ExportLogOut,
    OverviewOut,
    WatermarkTraceIn,
    WatermarkTraceOut,
)

router = APIRouter()

# 导出溯源仅对 园长 / 后勤 开放
_tracer = require_roles(ROLE_ADMIN, ROLE_LOGISTICS)


@router.get("/overview", response_model=OverviewOut, summary="园所资产总览")
def overview(
    within_days: int = Query(default=7, ge=0, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OverviewOut:
    return service.overview(db, user, within_days=within_days)


@router.get("/export", summary="导出报表（Excel，带可溯源暗水印）")
def export_report(
    within_days: int = Query(default=7, ge=0, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    data = service.overview(db, user, within_days=within_days)
    blob, code, detail = export.build_report_xlsx(data, user, within_days)
    db.add(
        ExportLog(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            kind="report",
            scope=getattr(user, "data_scope", ""),
            row_count=data.asset_total + len(data.due_soon),
            watermark=code,
            detail=detail,
        )
    )
    db.commit()
    filename = f"园务资产报表_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx"
    return StreamingResponse(
        iter([blob]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
            "X-Watermark-Code": code,
            "Access-Control-Expose-Headers": "X-Watermark-Code, Content-Disposition",
        },
    )


@router.post("/watermark/trace", response_model=WatermarkTraceOut, summary="水印溯源（反查导出人）")
def trace_watermark(
    payload: WatermarkTraceIn,
    db: Session = Depends(get_db),
    _: User = Depends(_tracer),
) -> WatermarkTraceOut:
    return WatermarkTraceOut(**export.trace_watermark(db, payload.code))


@router.get("/export-logs", response_model=list[ExportLogOut], summary="导出记录")
def export_logs(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(_tracer),
) -> list[ExportLog]:
    return list(
        db.scalars(select(ExportLog).order_by(ExportLog.id.desc()).limit(limit)).all()
    )
