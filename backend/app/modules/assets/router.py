"""资产模块 - 路由。"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.common.deps import ROLE_ADMIN, ROLE_LOGISTICS, get_current_user, require_roles
from app.core.database import get_db
from app.modules.assets import qrcode_svc, service
from app.modules.assets.models import Asset
from app.modules.assets.schemas import (
    AssetCreate,
    AssetOut,
    AssetUpdate,
    CategoryIn,
    CategoryOut,
    ScanCardOut,
    TagIn,
    TagOut,
    TagUpdate,
)
from app.modules.auth.models import User

router = APIRouter()

# 资产写操作角色：园长 / 后勤
_writer = require_roles(ROLE_ADMIN, ROLE_LOGISTICS)


@router.get("/categories", response_model=list[CategoryOut], summary="分类列表（树形）")
def list_categories(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return service.list_categories(db)


@router.post("/categories", response_model=CategoryOut, summary="新增分类")
def create_category(payload: CategoryIn, db: Session = Depends(get_db), _=Depends(_writer)):
    return service.create_category(db, payload)


@router.get("/tags", response_model=list[TagOut], summary="标签列表")
def list_tags(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return service.list_tags(db)


@router.post("/tags", response_model=TagOut, summary="新增标签")
def create_tag(payload: TagIn, db: Session = Depends(get_db), _=Depends(_writer)):
    return service.create_tag(db, payload.name, payload.domain)


@router.patch("/tags/{tag_id}", response_model=TagOut, summary="更新标签")
def update_tag(
    tag_id: int, payload: TagUpdate, db: Session = Depends(get_db), _=Depends(_writer)
):
    return service.update_tag(db, service.get_tag(db, tag_id), payload)


@router.delete("/tags/{tag_id}", summary="删除标签")
def delete_tag(tag_id: int, db: Session = Depends(get_db), _=Depends(_writer)) -> dict:
    service.delete_tag(db, service.get_tag(db, tag_id))
    return {"ok": True}


@router.get("", response_model=list[AssetOut], summary="资产列表（支持筛选）")
def list_assets(
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    domain: str | None = Query(default=None),
    tag_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Asset]:
    return service.list_assets(
        db, user, keyword=keyword, status=status, category_id=category_id, domain=domain, tag_id=tag_id
    )


@router.get("/{asset_id}", response_model=AssetOut, summary="资产详情")
def get_asset(
    asset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Asset:
    return service.get_asset(db, asset_id, user)


@router.post("", response_model=AssetOut, summary="新增资产")
def create_asset(
    payload: AssetCreate, db: Session = Depends(get_db), user: User = Depends(_writer)
) -> Asset:
    return service.create_asset(db, payload, user)


@router.patch("/{asset_id}", response_model=AssetOut, summary="更新资产")
def update_asset(
    asset_id: int, payload: AssetUpdate, db: Session = Depends(get_db), user: User = Depends(_writer)
) -> Asset:
    asset = service.get_asset(db, asset_id, user)
    return service.update_asset(db, asset, payload, user)


@router.delete("/{asset_id}", summary="删除资产")
def delete_asset(asset_id: int, db: Session = Depends(get_db), user: User = Depends(_writer)) -> dict:
    service.delete_asset(db, service.get_asset(db, asset_id, user), user)
    return {"ok": True}


@router.get("/scan/{token}", response_model=ScanCardOut, summary="扫码查询（公开只读，验签）")
def scan_asset(token: str, db: Session = Depends(get_db)) -> ScanCardOut:
    return ScanCardOut(**qrcode_svc.scan_card(db, token))


@router.get("/{asset_id}/qrcode", summary="资产二维码贴纸（PNG）")
def asset_qrcode(
    asset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Response:
    asset = service.get_asset(db, asset_id, user)
    org_name = qrcode_svc.root_org_name(db, asset.org_unit_id)
    info = qrcode_svc.build_info_text(asset, org_name)
    png = qrcode_svc.render_sticker(asset, org_name, info)
    return Response(
        content=png,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="asset_{asset.code}.png"'},
    )
