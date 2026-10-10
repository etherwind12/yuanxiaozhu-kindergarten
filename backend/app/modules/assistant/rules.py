"""AI 助手 —— 本地规则引擎。

未配置 DeepSeek Key 时独立完成「理解问题 → 查询 → 组织回答」；
配置了 Key 时仍作为数据检索底座与降级兜底。
所有查询强制走数据域过滤，AI 同样不能越权读取数据。
"""

import re
from datetime import date

from sqlalchemy import func, select

from app.common.scope import apply_org_scope, apply_owner_scope
from app.modules.assets.models import KIND_MAJOR, Asset, Category, Tag
from app.modules.borrow.models import STATUS_BORROWING, BorrowRecord
from app.modules.inspection.models import STATUS_PENDING, InspectionTask
from app.modules.inventory.models import TASK_OPEN, InventoryTask
from app.modules.report import service as report_service

STATUS_TEXT = {
    "in_stock": "在库",
    "borrowed": "借出",
    "repairing": "维修中",
    "scrapped": "已报废",
    "lost": "遗失",
}
TEXT_STATUS = {v: k for k, v in STATUS_TEXT.items()}
DOMAINS = ["健康", "语言", "社会", "科学", "艺术"]

# 大类别名，便于口语化提问（如「图书」→「图书绘本」）
CATEGORY_ALIASES = {
    "玩具": ["玩具", "积木", "拼图"],
    "教具": ["教具"],
    "图书绘本": ["图书", "绘本", "读物", "书"],
    "教学设备": ["教学设备", "多媒体", "一体机", "投影"],
    "电器家具": ["电器", "家具", "空调", "桌椅"],
    "体育器材": ["体育", "运动器材", "跳绳", "球类", "篮球"],
    "办公用品": ["办公"],
    "生活用品": ["生活用品", "被褥", "园服"],
    "消防安防": ["消防", "安防", "灭火器", "监控"],
}

HELP_WORDS = ["帮助", "你能做什么", "能做什么", "能干什么", "怎么用", "使用说明", "help", "你好", "hi", "hello", "介绍"]
EXAMPLES = [
    "园所资产总体情况",
    "有多少玩具",
    "在库资产有多少",
    "7 天内要消毒的资产有哪些",
    "哪些借用逾期未还",
    "有待处理的巡检吗",
    "进行中的盘点有几个",
]


def _hit(message: str, words: list[str]) -> bool:
    return any(w in message for w in words)


def _find_category(message: str) -> str | None:
    for major, aliases in CATEGORY_ALIASES.items():
        if any(a in message for a in aliases):
            return major
    return None


def _find_status(message: str) -> str | None:
    for text, key in TEXT_STATUS.items():
        if text in message:
            return key
    return None


def detect(message: str) -> tuple[str, dict]:
    """规则式意图识别，返回 (意图, 参数)。"""
    msg = message.strip()
    params: dict = {}
    m = re.search(r"(\d+)\s*天", msg)
    if m:
        params["within_days"] = int(m.group(1))
    if m and ("月" in msg):
        params["within_days"] = int(m.group(1)) * 30

    if _hit(msg, HELP_WORDS):
        return "help", params
    if "盘点" in msg:
        return "inventory_open", params
    if _hit(msg, ["巡检", "检查任务", "待处理"]):
        return "inspection_pending", params
    if _hit(msg, ["逾期", "超期", "未还", "没还", "没归还"]):
        return "overdue_borrow", params
    if _hit(msg, ["到期", "该消毒", "该检查", "临近", "快到期", "要消毒", "要检查"]):
        return "list_due", params
    if _hit(msg, ["借出", "借了", "在借", "谁借", "借用"]):
        return "borrowing_list", params
    if _hit(msg, ["总览", "概况", "整体", "汇总", "总体", "基本情况", "情况如何"]):
        return "overview", params

    if (cat := _find_category(msg)):
        params["category"] = cat
    if (st := _find_status(msg)):
        params["status"] = st
    if (dom := next((d for d in DOMAINS if d in msg), None)):
        params["domain"] = dom
    return "count_assets", params


def _scoped(stmt, model, db, user, *owner_fields: str):
    stmt = apply_org_scope(stmt, model, db, user)
    if owner_fields:
        stmt = apply_owner_scope(stmt, model, user, *owner_fields)
    return stmt


def _category_ids(db, major_name: str) -> list[int]:
    cats = db.scalars(select(Category)).all()
    major = next((c for c in cats if c.name == major_name and c.kind == KIND_MAJOR), None)
    if not major:
        return []
    return [major.id] + [c.id for c in cats if c.parent_id == major.id]


# ---------------- 意图处理 ----------------

def _help(db, user, params):
    return {
        "reply": "我是园小助 AI 助手，可以帮你查询资产与园务数据。试试这些问题：",
        "examples": EXAMPLES,
    }


def _overview(db, user, params):
    ov = report_service.overview(db, user, within_days=params.get("within_days", 7))
    data = [
        {"label": "资产总数", "value": ov.asset_total},
        {"label": "借出中", "value": ov.borrowing_count},
        {"label": "逾期未还", "value": ov.overdue_borrow_count},
        {"label": "待处理巡检", "value": ov.inspection_pending},
        {"label": "巡检已逾期", "value": ov.inspection_overdue},
        {"label": "进行中盘点", "value": ov.inventory_open},
    ]
    chart = [{"name": STATUS_TEXT.get(k, k), "count": v} for k, v in ov.status_counts.items() if v]
    reply = (
        f"当前共 {ov.asset_total} 件资产；借出中 {ov.borrowing_count} 笔，其中逾期未还 "
        f"{ov.overdue_borrow_count} 笔；待处理巡检 {ov.inspection_pending} 项（已逾期 "
        f"{ov.inspection_overdue} 项）；进行中盘点 {ov.inventory_open} 个。"
    )
    return {"reply": reply, "data": data, "chart": chart}


def _count_assets(db, user, params):
    cat, st, dom = params.get("category"), params.get("status"), params.get("domain")
    stmt = select(func.count(Asset.id))
    if cat:
        stmt = stmt.where(Asset.category_id.in_(_category_ids(db, cat) or [-1]))
    if st:
        stmt = stmt.where(Asset.status == st)
    if dom:
        stmt = stmt.where(Asset.tags.any(Tag.domain == dom))
    count = db.scalar(apply_org_scope(stmt, Asset, db, user)) or 0

    parts = []
    if cat:
        parts.append(f"分类「{cat}」")
    if st:
        parts.append(f"状态「{STATUS_TEXT[st]}」")
    if dom:
        parts.append(f"领域「{dom}」")
    scope_desc = "、".join(parts) if parts else "你可见范围内"
    return {
        "reply": f"{scope_desc}的资产共 {count} 件。",
        "data": [{"label": "匹配资产数", "value": count}],
    }


def _list_due(db, user, params):
    days = params.get("within_days", 7)
    ov = report_service.overview(db, user, within_days=days)
    if not ov.due_soon:
        return {"reply": f"未来 {days} 天内没有消毒 / 安全检查到期事项。",
                "table": {"columns": ["资产", "类型", "到期日", "剩余"], "rows": []}}
    rows = [
        [i.asset_name, "消毒" if i.type == "disinfect" else "安全检查", str(i.due_date),
         f"逾期 {abs(i.days_left)} 天" if i.days_left < 0 else f"{i.days_left} 天"]
        for i in ov.due_soon[:20]
    ]
    return {
        "reply": f"未来 {days} 天内有 {len(ov.due_soon)} 项消毒 / 安全检查到期，列出前 {len(rows)} 项：",
        "table": {"columns": ["资产", "类型", "到期日", "剩余"], "rows": rows},
    }


def _overdue_borrow(db, user, params):
    stmt = select(BorrowRecord).where(
        BorrowRecord.status == STATUS_BORROWING,
        BorrowRecord.due_at.is_not(None),
        BorrowRecord.due_at < date.today(),
    )
    rows = list(db.scalars(_scoped(stmt, BorrowRecord, db, user, "borrower_id")).all())
    if not rows:
        return {"reply": "当前没有逾期未还的借出记录。",
                "table": {"columns": ["资产", "借用人", "应还日期", "逾期"], "rows": []}}
    table_rows = [
        [r.asset.name if r.asset else "—",
         (r.borrower.full_name or r.borrower.username) if r.borrower else "—",
         str(r.due_at), f"{(date.today() - r.due_at).days} 天"]
        for r in rows
    ]
    return {"reply": f"当前有 {len(rows)} 笔借用已逾期未还：",
            "table": {"columns": ["资产", "借用人", "应还日期", "逾期"], "rows": table_rows}}


def _borrowing_list(db, user, params):
    stmt = select(BorrowRecord).where(BorrowRecord.status == STATUS_BORROWING)
    rows = list(db.scalars(_scoped(stmt, BorrowRecord, db, user, "borrower_id")).all())
    if not rows:
        return {"reply": "当前没有借出中的记录。",
                "table": {"columns": ["资产", "借用人", "借出日期", "应还日期"], "rows": []}}
    table_rows = [
        [r.asset.name if r.asset else "—",
         (r.borrower.full_name or r.borrower.username) if r.borrower else "—",
         r.borrow_at.strftime("%Y-%m-%d") if r.borrow_at else "—",
         str(r.due_at) if r.due_at else "—"]
        for r in rows[:20]
    ]
    return {"reply": f"当前共有 {len(rows)} 笔借出中记录：",
            "table": {"columns": ["资产", "借用人", "借出日期", "应还日期"], "rows": table_rows}}


def _inspection_pending(db, user, params):
    stmt = select(InspectionTask).where(InspectionTask.status == STATUS_PENDING)
    rows = list(db.scalars(_scoped(stmt, InspectionTask, db, user, "created_by", "assignee_id")).all())
    if not rows:
        return {"reply": "当前没有待处理的巡检任务。", "data": [{"label": "待处理巡检", "value": 0}]}
    overdue = sum(1 for r in rows if r.due_date and r.due_date < date.today())
    table_rows = [
        [r.title, "消毒" if r.type == "disinfect" else "安全检查",
         (r.assignee.full_name or r.assignee.username) if r.assignee else "—",
         str(r.due_date) if r.due_date else "—"]
        for r in rows[:20]
    ]
    return {"reply": f"当前有 {len(rows)} 项待处理巡检，其中 {overdue} 项已逾期：",
            "table": {"columns": ["任务", "类型", "负责人", "到期日"], "rows": table_rows}}


def _inventory_open(db, user, params):
    stmt = select(InventoryTask).where(InventoryTask.status == TASK_OPEN)
    rows = list(db.scalars(_scoped(stmt, InventoryTask, db, user, "created_by")).all())
    if not rows:
        return {"reply": "当前没有进行中的盘点任务。", "data": [{"label": "进行中盘点", "value": 0}]}
    return {"reply": f"当前有 {len(rows)} 个进行中的盘点任务。",
            "data": [{"label": "进行中盘点", "value": len(rows)}]}


_HANDLERS = {
    "help": _help,
    "overview": _overview,
    "count_assets": _count_assets,
    "list_due": _list_due,
    "overdue_borrow": _overdue_borrow,
    "borrowing_list": _borrowing_list,
    "inspection_pending": _inspection_pending,
    "inventory_open": _inventory_open,
}


def answer(db, user, message: str) -> dict:
    intent, params = detect(message)
    return _HANDLERS[intent](db, user, params)
