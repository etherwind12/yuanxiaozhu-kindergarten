"""组织与数据域模块 - 业务逻辑。"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.org.models import ORG_TYPES, OrgUnit
from app.modules.org.schemas import OrgUnitIn, OrgUnitOut, OrgUnitUpdate


def create_unit(db: Session, data: OrgUnitIn) -> OrgUnit:
    if data.type not in ORG_TYPES:
        raise HTTPException(status_code=400, detail=f"组织域类型不合法，可选：{ORG_TYPES}")
    if data.parent_id is not None and not db.get(OrgUnit, data.parent_id):
        raise HTTPException(status_code=400, detail="上级组织域不存在")
    obj = OrgUnit(name=data.name, parent_id=data.parent_id, type=data.type)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_unit(db: Session, unit: OrgUnit, data: OrgUnitUpdate) -> OrgUnit:
    if data.type is not None and data.type not in ORG_TYPES:
        raise HTTPException(status_code=400, detail="组织域类型不合法")
    if data.parent_id is not None:
        if data.parent_id == unit.id:
            raise HTTPException(status_code=400, detail="上级组织域不能为自身")
        if not db.get(OrgUnit, data.parent_id):
            raise HTTPException(status_code=400, detail="上级组织域不存在")
    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(unit, field, value)
    db.commit()
    db.refresh(unit)
    return unit


def get_unit(db: Session, unit_id: int) -> OrgUnit:
    unit = db.get(OrgUnit, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="组织域不存在")
    return unit


def list_tree(db: Session) -> list[OrgUnitOut]:
    """返回组织树（园区 → 楼栋 → 班级）。"""
    units = list(db.scalars(select(OrgUnit).order_by(OrgUnit.id)))
    nodes = {
        u.id: OrgUnitOut(id=u.id, name=u.name, parent_id=u.parent_id, type=u.type, children=[])
        for u in units
    }
    roots: list[OrgUnitOut] = []
    for u in units:
        node = nodes[u.id]
        if u.parent_id and u.parent_id in nodes:
            nodes[u.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots
