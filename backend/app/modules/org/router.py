"""组织与数据域模块 - 路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.deps import ROLE_ADMIN, get_current_user, require_roles
from app.core.database import get_db
from app.modules.org import service
from app.modules.org.schemas import OrgUnitIn, OrgUnitOut, OrgUnitUpdate

router = APIRouter()

_admin = require_roles(ROLE_ADMIN)


@router.get("/units", response_model=list[OrgUnitOut], summary="组织树（园区/楼栋/班级）")
def list_units(db: Session = Depends(get_db), _=Depends(get_current_user)) -> list[OrgUnitOut]:
    return service.list_tree(db)


@router.post("/units", response_model=OrgUnitOut, summary="新建组织域")
def create_unit(
    payload: OrgUnitIn, db: Session = Depends(get_db), _=Depends(_admin)
) -> OrgUnitOut:
    unit = service.create_unit(db, payload)
    return OrgUnitOut.model_validate(unit)


@router.patch("/units/{unit_id}", response_model=OrgUnitOut, summary="更新组织域")
def update_unit(
    unit_id: int, payload: OrgUnitUpdate, db: Session = Depends(get_db), _=Depends(_admin)
) -> OrgUnitOut:
    unit = service.update_unit(db, service.get_unit(db, unit_id), payload)
    return OrgUnitOut.model_validate(unit)
