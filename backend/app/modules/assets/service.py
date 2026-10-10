"""资产模块 - 业务逻辑。"""

from fastapi import HTTPException
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.common.scope import apply_org_scope, ensure_org_scope, ensure_org_unit_allowed
from app.modules.assets.models import (
    DOMAINS,
    KIND_MAJOR,
    KIND_SUB,
    ASSET_STATUSES,
    Asset,
    Category,
    Tag,
    asset_tags,
)
from app.modules.assets.schemas import CategoryOut
from app.modules.borrow.models import STATUS_BORROWING, BorrowRecord
from app.modules.org.models import OrgUnit


# ---------- 分类 ----------
def create_category(db: Session, data) -> Category:
    if data.kind not in (KIND_MAJOR, KIND_SUB):
        raise HTTPException(status_code=400, detail="分类层级不合法（major / sub）")
    if db.scalar(select(Category).where(Category.name == data.name)):
        raise HTTPException(status_code=400, detail="分类已存在")
    if data.parent_id is not None and not db.get(Category, data.parent_id):
        raise HTTPException(status_code=400, detail="上级分类不存在")
    obj = Category(name=data.name, parent_id=data.parent_id, kind=data.kind, description=data.description)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_categories(db: Session) -> list[CategoryOut]:
    """返回树形分类：资产大类 → 子类。"""
    rows = list(db.scalars(select(Category).order_by(Category.id)))
    nodes = {
        c.id: CategoryOut(
            id=c.id, name=c.name, parent_id=c.parent_id, kind=c.kind,
            description=c.description, children=[],
        )
        for c in rows
    }
    roots: list[CategoryOut] = []
    for c in rows:
        node = nodes[c.id]
        if c.parent_id and c.parent_id in nodes:
            nodes[c.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots


# ---------- 标签 ----------
def _check_domain(domain: str) -> str:
    """领域必须取自五大领域（与 meta 字典同源）。"""
    if domain not in DOMAINS:
        raise HTTPException(status_code=400, detail="领域不合法")
    return domain


def create_tag(db: Session, name: str, domain: str) -> Tag:
    name = (name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="标签名称不能为空")
    _check_domain(domain)
    if db.scalar(select(Tag).where(Tag.name == name)):
        raise HTTPException(status_code=400, detail="标签已存在")
    obj = Tag(name=name, domain=domain)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_tag(db: Session, tag_id: int) -> Tag:
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    return tag


def update_tag(db: Session, tag: Tag, data) -> Tag:
    payload = data.model_dump(exclude_unset=True)
    if "name" in payload:
        name = (payload["name"] or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="标签名称不能为空")
        if db.scalar(select(Tag).where(Tag.name == name, Tag.id != tag.id)):
            raise HTTPException(status_code=400, detail="标签已存在")
        tag.name = name
    if "domain" in payload:
        tag.domain = _check_domain(payload["domain"])
    db.commit()
    db.refresh(tag)
    return tag


def delete_tag(db: Session, tag: Tag) -> None:
    """删除标签并解除其在资产上的引用（不删除资产本体）。"""
    db.execute(delete(asset_tags).where(asset_tags.c.tag_id == tag.id))
    db.delete(tag)
    db.commit()


def list_tags(db: Session) -> list[Tag]:
    return list(db.scalars(select(Tag).order_by(Tag.id)))


# ---------- 资产编号 ----------
def _next_code(db: Session) -> str:
    """取现有编号的最大序号 +1，避免删除资产后与残留编号冲突。"""
    max_no = 0
    for code in db.scalars(select(Asset.code)):
        if code and code.startswith("ZC"):
            try:
                max_no = max(max_no, int(code[2:]))
            except ValueError:
                continue
    return f"ZC{max_no + 1:05d}"


def _get_tags(db: Session, tag_ids: list[int]) -> list[Tag]:
    if not tag_ids:
        return []
    tags = list(db.scalars(select(Tag).where(Tag.id.in_(tag_ids))))
    if len(tags) != len(set(tag_ids)):
        raise HTTPException(status_code=400, detail="存在无效的标签")
    return tags


# ---------- 资产 ----------
def create_asset(db: Session, data, user) -> Asset:
    code = data.code or _next_code(db)
    if db.scalar(select(Asset).where(Asset.code == code)):
        raise HTTPException(status_code=400, detail="资产编号已存在")
    org_unit_id = data.org_unit_id if data.org_unit_id is not None else user.org_unit_id
    if org_unit_id is not None and not db.get(OrgUnit, org_unit_id):
        raise HTTPException(status_code=400, detail="组织域不存在")
    ensure_org_unit_allowed(db, user, org_unit_id, "资产归属域")
    asset = Asset(
        name=data.name,
        code=code,
        category_id=data.category_id,
        org_unit_id=org_unit_id,
        quantity=data.quantity,
        unit=data.unit,
        location=data.location,
        age_range=data.age_range,
        safety_level=data.safety_level,
        purchase_date=data.purchase_date,
        disinfect_due=data.disinfect_due,
        safety_check_due=data.safety_check_due,
        remark=data.remark,
        tags=_get_tags(db, data.tag_ids),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def update_asset(db: Session, asset: Asset, data, user) -> Asset:
    ensure_org_scope(db, asset, user, "资产")
    payload = data.model_dump(exclude_unset=True)
    if "tag_ids" in payload:
        asset.tags = _get_tags(db, payload.pop("tag_ids"))
    if "status" in payload and payload["status"] not in ASSET_STATUSES:
        raise HTTPException(status_code=400, detail="资产状态不合法")
    if "org_unit_id" in payload and payload["org_unit_id"] is not None:
        if not db.get(OrgUnit, payload["org_unit_id"]):
            raise HTTPException(status_code=400, detail="组织域不存在")
        ensure_org_unit_allowed(db, user, payload["org_unit_id"], "资产归属域")
    for field, value in payload.items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return asset


def delete_asset(db: Session, asset: Asset, user) -> None:
    ensure_org_scope(db, asset, user, "资产")
    active = db.scalar(
        select(BorrowRecord).where(
            BorrowRecord.asset_id == asset.id, BorrowRecord.status == STATUS_BORROWING
        )
    )
    if active:
        raise HTTPException(status_code=400, detail="该资产正在借出中，请先归还后再删除")
    db.delete(asset)
    db.commit()


def get_asset(db: Session, asset_id: int, user=None) -> Asset:
    asset = db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    if user is not None:
        ensure_org_scope(db, asset, user, "资产")
    return asset


def list_assets(
    db: Session,
    user,
    *,
    keyword: str | None = None,
    status: str | None = None,
    category_id: int | None = None,
    domain: str | None = None,
    tag_id: int | None = None,
) -> list[Asset]:
    stmt = select(Asset)
    stmt = apply_org_scope(stmt, Asset, db, user)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Asset.name.like(like), Asset.code.like(like), Asset.location.like(like)))
    if status:
        stmt = stmt.where(Asset.status == status)
    if category_id:
        stmt = stmt.where(Asset.category_id == category_id)
    if tag_id:
        stmt = stmt.where(Asset.tags.any(Tag.id == tag_id))
    if domain:
        stmt = stmt.where(Asset.tags.any(Tag.domain == domain))
    stmt = stmt.order_by(Asset.id.desc())
    return list(db.scalars(stmt))
