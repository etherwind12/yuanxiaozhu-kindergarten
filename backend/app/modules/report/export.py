"""报表导出：生成带分层暗水印的 Excel，并支持水印反查溯源。

水印分三处埋入，均为「服务端签名 + 可校验」：
1. 文件属性层（wb.properties）——改内容也改不掉；
2. 隐形单元格层（最右列 XFD，白色字体 + 宽度 0）；
3. 打印页脚层（页脚可见小字，体现「内部资料」）。
水印码 = short_code(详情串)，篡改任一环节都会导致溯源校验失败。
"""

from datetime import datetime, timezone
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from sqlalchemy import select

from app.core.sign import short_code

_WM_COL = 16384  # Excel 最右列 XFD
_HEAD_FILL = PatternFill("solid", fgColor="0E6B5C")
_HEAD_FONT = Font(color="FFFFFF", bold=True)

_STATUS_NAMES = {
    "in_stock": "在库",
    "borrowed": "借出",
    "repairing": "维修中",
    "scrapped": "已报废",
    "lost": "遗失",
}


def _detail(user, scope: str, row_count: int) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return f"{user.id}|{user.username}|{scope}|{row_count}|{ts}"


def _head(ws, headers: list[str]) -> None:
    ws.append(headers)
    for idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=idx)
        cell.fill = _HEAD_FILL
        cell.font = _HEAD_FONT
        cell.alignment = Alignment(horizontal="center")


def _mark(ws, code: str) -> None:
    ws.cell(row=1, column=_WM_COL, value=f"YXZ-WM:{code}").font = Font(color="FFFFFF", size=1)
    ws.column_dimensions[get_column_letter(_WM_COL)].width = 0
    ws.oddFooter.center.text = f"内部资料 · 水印 {code} · 严禁外传"
    ws.oddFooter.center.size = 7


def build_report_xlsx(data, user, within_days: int) -> tuple[bytes, str, str]:
    """返回 (xlsx 字节, 水印码, 水印详情串)。"""
    scope = getattr(user, "data_scope", "")
    row_count = data.asset_total + len(data.due_soon)
    detail = _detail(user, scope, row_count)
    code = short_code(detail)

    wb = Workbook()

    ws = wb.active
    ws.title = "总览"
    _head(ws, ["指标", "数值"])
    for label, value in [
        ("资产总数", data.asset_total),
        ("借出中", data.borrowing_count),
        ("逾期未还", data.overdue_borrow_count),
        ("待处理巡检", data.inspection_pending),
        ("巡检已逾期", data.inspection_overdue),
        ("进行中盘点", data.inventory_open),
        ("预警范围（天）", within_days),
        ("导出人", user.full_name or user.username),
        ("导出时间", datetime.now().strftime("%Y-%m-%d %H:%M")),
    ]:
        ws.append([label, value])
    _mark(ws, code)

    ws = wb.create_sheet("状态分布")
    _head(ws, ["状态", "数量"])
    for key, count in data.status_counts.items():
        ws.append([_STATUS_NAMES.get(key, key), count])
    _mark(ws, code)

    ws = wb.create_sheet("分类统计")
    _head(ws, ["资产大类", "数量"])
    for item in data.by_category:
        ws.append([item.name, item.count])
    _mark(ws, code)

    ws = wb.create_sheet("领域分布")
    _head(ws, ["领域", "数量"])
    for item in data.by_domain:
        ws.append([item.name, item.count])
    _mark(ws, code)

    ws = wb.create_sheet("到期预警")
    _head(ws, ["资产", "类型", "到期日", "剩余天数"])
    for item in data.due_soon:
        ws.append([
            item.asset_name,
            "消毒" if item.type == "disinfect" else "安全检查",
            str(item.due_date),
            item.days_left,
        ])
    _mark(ws, code)

    wb.properties.creator = f"园小助 · {code}"
    wb.properties.lastModifiedBy = f"YXZ-{code}"
    wb.properties.title = f"园务资产报表 {code}"
    wb.properties.description = f"内部导出件，水印码 {code}；对外传播可据此溯源。"

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue(), code, detail


def trace_watermark(db, code: str) -> dict:
    """水印反查：定位导出人，并二次校验签名完整性。"""
    from app.modules.report.models import ExportLog  # 延迟导入，避免循环

    log = db.scalars(
        select(ExportLog).where(ExportLog.watermark == code.strip().upper()).order_by(ExportLog.id.desc())
    ).first()
    if not log:
        return {"valid": False, "message": "未找到该水印码对应的导出记录，可能为伪造或已失。".replace("已失。", "已失效。")}
    if short_code(log.detail) != log.watermark:
        return {"valid": False, "message": "水印校验失败：签名与记录不一致，疑似被篡改。"}
    return {
        "valid": True,
        "username": log.username,
        "full_name": log.full_name,
        "exported_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "scope": log.scope or "—",
        "row_count": log.row_count,
        "message": "水印有效，已定位到导出来源。",
    }
