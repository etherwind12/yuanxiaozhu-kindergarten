"""资产模块 - 数据传输对象。"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    parent_id: int | None = None
    kind: str = "major"  # major 资产大类 / sub 子类
    description: str = ""


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None = None
    kind: str = "major"
    description: str
    children: list["CategoryOut"] = []


CategoryOut.model_rebuild()


class TagIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    domain: str = ""


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    domain: str | None = None


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    domain: str


class AssetBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category_id: int | None = None
    org_unit_id: int | None = None   # 归属数据域，留空则取当前用户所属域
    quantity: int = 1
    unit: str = "件"
    location: str = ""
    age_range: str = ""
    safety_level: str = ""
    purchase_date: date | None = None
    disinfect_due: date | None = None
    safety_check_due: date | None = None
    remark: str = ""
    tag_ids: list[int] = []


class AssetCreate(AssetBase):
    code: str | None = None  # 留空则自动生成


class AssetUpdate(BaseModel):
    name: str | None = None
    category_id: int | None = None
    org_unit_id: int | None = None
    status: str | None = None
    quantity: int | None = None
    unit: str | None = None
    location: str | None = None
    age_range: str | None = None
    safety_level: str | None = None
    purchase_date: date | None = None
    disinfect_due: date | None = None
    safety_check_due: date | None = None
    remark: str | None = None
    tag_ids: list[int] | None = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    org_unit_id: int | None = None
    status: str
    quantity: int
    unit: str = "件"
    location: str
    age_range: str
    safety_level: str
    purchase_date: date | None
    disinfect_due: date | None
    safety_check_due: date | None
    remark: str
    created_at: datetime
    category: CategoryOut | None = None
    tags: list[TagOut] = []


class ScanCardOut(BaseModel):
    """扫码落地卡片：仅暴露非敏感字段。"""

    valid: bool
    message: str = ""
    id: int | None = None
    name: str = ""
    code: str = ""
    status: str = ""
    status_text: str = ""
    status_tone: str = "default"
    category: str = ""
    org_name: str = ""
    location: str = ""
    quantity: int = 0
    unit: str = ""
    safety_level: str = ""
    age_range: str = ""
