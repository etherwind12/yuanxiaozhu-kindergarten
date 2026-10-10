"""数据域（分域）过滤工具。

设计约束：所有列表 / 详情查询在 service 层**强制注入**域过滤条件，
跨域读取或写入直接返回 403。

数据范围 `data_scope`：
- all  全园：不限制域
- org  本域及下级：用户所属组织域及其所有子孙域
- self 仅本人：本人所属组织域（精确），且记录类数据额外限定「仅本人相关」
"""

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.org.models import OrgUnit

SCOPE_ALL = "all"
SCOPE_ORG = "org"
SCOPE_SELF = "self"
DATA_SCOPES = [SCOPE_ALL, SCOPE_ORG, SCOPE_SELF]


def _subtree_ids(db: Session, root_id: int) -> set[int]:
    """返回 root_id 及其所有子孙组织域 id。"""
    children: dict[int, list[int]] = {}
    for uid, parent_id in db.execute(select(OrgUnit.id, OrgUnit.parent_id)).all():
        children.setdefault(parent_id, []).append(uid)
    result: set[int] = set()
    stack = [root_id]
    while stack:
        current = stack.pop()
        if current in result:
            continue
        result.add(current)
        stack.extend(children.get(current, []))
    return result


def visible_org_unit_ids(db: Session, user: User) -> set[int] | None:
    """计算用户可见的组织域集合；返回 None 表示不限制（全园）。"""
    scope = getattr(user, "data_scope", SCOPE_ALL)
    if scope == SCOPE_ALL:
        return None
    if user.org_unit_id is None:
        return set()
    if scope == SCOPE_ORG:
        return _subtree_ids(db, user.org_unit_id)
    # self：仅本人所属域（精确）
    return {user.org_unit_id}


def apply_org_scope(stmt, model, db: Session, user: User):
    """给查询语句注入组织域过滤（模型需含 org_unit_id 字段）。"""
    ids = visible_org_unit_ids(db, user)
    if ids is None:
        return stmt
    return stmt.where(model.org_unit_id.in_(ids))


def ensure_org_scope(db: Session, obj, user: User, name: str = "数据") -> None:
    """校验对象是否落在用户数据域内，否则 403。"""
    ids = visible_org_unit_ids(db, user)
    if ids is None:
        return
    if getattr(obj, "org_unit_id", None) not in ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"无权访问该{name}（超出数据域）")


def apply_owner_scope(stmt, model, user: User, *owner_fields: str):
    """self 范围时，进一步限定「仅本人相关」的记录（任一归属字段匹配即保留）。"""
    if getattr(user, "data_scope", SCOPE_ALL) != SCOPE_SELF or not owner_fields:
        return stmt
    return stmt.where(or_(*[getattr(model, field) == user.id for field in owner_fields]))


def ensure_owner_scope(obj, user: User, *owner_fields: str, name: str = "数据") -> None:
    """self 范围时校验对象归属：任一归属字段等于本人即放行，否则 403。"""
    if getattr(user, "data_scope", SCOPE_ALL) != SCOPE_SELF:
        return
    if any(getattr(obj, field, None) == user.id for field in owner_fields):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"无权操作该{name}（非本人数据）")


def ensure_org_unit_allowed(db: Session, user: User, org_unit_id: int | None, name: str = "组织域") -> None:
    """写入归属前校验目标组织域是否在用户可见数据域内，越域 403。"""
    if org_unit_id is None:
        return
    ids = visible_org_unit_ids(db, user)
    if ids is None:
        return
    if org_unit_id not in ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"无权将{name}设置到数据域之外")
