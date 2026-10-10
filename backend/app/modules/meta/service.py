"""系统字典的权威定义。

前端所有枚举展示（状态、类型、领域、数据域、组织类型、角色与权限）
一律由本模块下发，避免前后端各留一份字典造成漂移。
"""

from app.common.deps import ROLE_ADMIN, ROLE_CAREGIVER, ROLE_LOGISTICS, ROLE_TEACHER
from app.common.scope import SCOPE_ALL, SCOPE_ORG, SCOPE_SELF
from app.modules.assets import models as asset_models
from app.modules.borrow import models as borrow_models
from app.modules.inspection import models as inspection_models
from app.modules.inventory import models as inventory_models
from app.modules.org import models as org_models
from app.modules.teaching import models as teaching_models

# 每项为 (值, 中文名, 前端标签色调)
ASSET_STATUS = [
    (asset_models.STATUS_IN_STOCK, "在库", "ok"),
    (asset_models.STATUS_BORROWED, "借出", "warn"),
    (asset_models.STATUS_REPAIRING, "维修中", "info"),
    (asset_models.STATUS_SCRAPPED, "已报废", "muted"),
    (asset_models.STATUS_LOST, "遗失", "danger"),
]

BORROW_STATUS = [
    (borrow_models.STATUS_BORROWING, "借用中", "warn"),
    (borrow_models.STATUS_RETURNED, "已归还", "ok"),
]

INVENTORY_TASK_STATUS = [
    (inventory_models.TASK_OPEN, "盘点中", "info"),
    (inventory_models.TASK_FINISHED, "已结束", "muted"),
]

INVENTORY_RESULT = [
    (inventory_models.RESULT_PENDING, "未盘", "muted"),
    (inventory_models.RESULT_MATCHED, "相符", "ok"),
    (inventory_models.RESULT_DIFF, "差异", "danger"),
]

INSPECTION_TYPE = [
    (inspection_models.TYPE_DISINFECT, "消毒", "info"),
    (inspection_models.TYPE_SAFETY, "安全检查", "warn"),
]

INSPECTION_STATUS = [
    (inspection_models.STATUS_PENDING, "待处理", "warn"),
    (inspection_models.STATUS_DONE, "已完成", "ok"),
]

INSPECTION_RESULT = [
    (inspection_models.RESULT_PASS, "合格", "ok"),
    (inspection_models.RESULT_FAIL, "不合格", "danger"),
]

RESERVATION_STATUS = [
    (teaching_models.STATUS_PENDING, "待审批", "warn"),
    (teaching_models.STATUS_APPROVED, "已通过", "ok"),
    (teaching_models.STATUS_REJECTED, "已驳回", "danger"),
    (teaching_models.STATUS_FINISHED, "已结束", "muted"),
]

DATA_SCOPE = [
    (SCOPE_ALL, "全园", "default"),
    (SCOPE_ORG, "本部门", "default"),
    (SCOPE_SELF, "仅本人", "default"),
]

ORG_TYPE = [
    (org_models.TYPE_PARK, "园区", "default"),
    (org_models.TYPE_BUILDING, "楼栋", "default"),
    (org_models.TYPE_CLASS, "班级", "default"),
]

# 幼儿园五大领域与 assets 模块同源
DOMAIN = [(d, d, "default") for d in asset_models.DOMAINS]

# 角色中文名
ROLE_NAMES = {
    ROLE_ADMIN: "园长",
    ROLE_LOGISTICS: "后勤",
    ROLE_TEACHER: "教师",
    ROLE_CAREGIVER: "保育员",
}

# 各角色的功能权限，前端菜单据此渲染；接口鉴权仍由 require_roles 独立兜底
PERMISSIONS = {
    ROLE_ADMIN: [
        "asset:view", "asset:write", "borrow", "inventory", "inspection",
        "reserve:apply", "reserve:approve", "report", "report:trace",
        "user:manage", "org:manage",
    ],
    ROLE_LOGISTICS: [
        "asset:view", "asset:write", "borrow", "inventory", "inspection",
        "reserve:apply", "reserve:approve", "report", "report:trace",
    ],
    ROLE_TEACHER: ["asset:view", "borrow", "reserve:apply", "report"],
    ROLE_CAREGIVER: ["asset:view", "borrow", "inventory", "inspection", "report"],
}

_ASSET_STATUS_TEXT = {value: text for value, text, _ in ASSET_STATUS}
_ASSET_STATUS_TONE = {value: tone for value, _, tone in ASSET_STATUS}
_BORROW_STATUS_TEXT = {value: text for value, text, _ in BORROW_STATUS}
_BORROW_STATUS_TONE = {value: tone for value, _, tone in BORROW_STATUS}
_INSPECTION_STATUS_TEXT = {value: text for value, text, _ in INSPECTION_STATUS}
_INSPECTION_STATUS_TONE = {value: tone for value, _, tone in INSPECTION_STATUS}

# 派生展示态：状态值本身无法表达「逾期」，由后端统一叠加，前端不再写死文案
BORROW_OVERDUE_TEXT = "逾期未还"
INSPECTION_OVERDUE_TEXT = "已逾期"


def asset_status_text(code: str) -> str:
    """资产状态中文名，供扫码落地页等公开接口使用。"""
    return _ASSET_STATUS_TEXT.get(code, code)


def asset_status_tone(code: str) -> str:
    """资产状态对应的标签色调，供扫码落地页等公开接口使用。"""
    return _ASSET_STATUS_TONE.get(code, "default")


def borrow_status_text(status: str, overdue: bool) -> str:
    if overdue and status == borrow_models.STATUS_BORROWING:
        return BORROW_OVERDUE_TEXT
    return _BORROW_STATUS_TEXT.get(status, status)


def borrow_status_tone(status: str, overdue: bool) -> str:
    if overdue and status == borrow_models.STATUS_BORROWING:
        return "danger"
    return _BORROW_STATUS_TONE.get(status, "default")


def inspection_status_text(status: str, overdue: bool) -> str:
    if overdue and status == inspection_models.STATUS_PENDING:
        return INSPECTION_OVERDUE_TEXT
    return _INSPECTION_STATUS_TEXT.get(status, status)


def inspection_status_tone(status: str, overdue: bool) -> str:
    if overdue and status == inspection_models.STATUS_PENDING:
        return "danger"
    return _INSPECTION_STATUS_TONE.get(status, "default")


_INSPECTION_TYPE_TEXT = {value: text for value, text, _ in INSPECTION_TYPE}
_INSPECTION_TYPE_TONE = {value: tone for value, _, tone in INSPECTION_TYPE}
_INSPECTION_RESULT_TEXT = {value: text for value, text, _ in INSPECTION_RESULT}
_INSPECTION_RESULT_TONE = {value: tone for value, _, tone in INSPECTION_RESULT}


def inspection_type_text(code: str) -> str:
    return _INSPECTION_TYPE_TEXT.get(code, code)


def inspection_type_tone(code: str) -> str:
    return _INSPECTION_TYPE_TONE.get(code, "default")


def inspection_result_text(code: str) -> str:
    return _INSPECTION_RESULT_TEXT.get(code, code)


def inspection_result_tone(code: str) -> str:
    return _INSPECTION_RESULT_TONE.get(code, "default")


def _opts(rows: list[tuple[str, str, str]]) -> list[dict]:
    return [{"value": value, "text": text, "tone": tone} for value, text, tone in rows]


def build() -> dict:
    return {
        "asset_status": _opts(ASSET_STATUS),
        "borrow_status": _opts(BORROW_STATUS),
        "inventory_task_status": _opts(INVENTORY_TASK_STATUS),
        "inventory_result": _opts(INVENTORY_RESULT),
        "inspection_type": _opts(INSPECTION_TYPE),
        "inspection_status": _opts(INSPECTION_STATUS),
        "inspection_result": _opts(INSPECTION_RESULT),
        "reservation_status": _opts(RESERVATION_STATUS),
        "domain": _opts(DOMAIN),
        "data_scope": _opts(DATA_SCOPE),
        "org_type": _opts(ORG_TYPE),
        "role": [{"value": key, "name": name} for key, name in ROLE_NAMES.items()],
        "permissions": PERMISSIONS,
    }
