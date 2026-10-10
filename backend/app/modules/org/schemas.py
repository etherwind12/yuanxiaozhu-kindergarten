"""组织与数据域模块 - 数据传输对象。"""

from pydantic import BaseModel, ConfigDict, Field


class OrgUnitIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    parent_id: int | None = None
    type: str = "class"


class OrgUnitUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None
    type: str | None = None


class OrgUnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None
    type: str
    children: list["OrgUnitOut"] = []


OrgUnitOut.model_rebuild()
