"""元数据（字典）模块 - 数据传输对象。"""

from pydantic import BaseModel


class DictOption(BaseModel):
    value: str
    text: str
    tone: str = "default"


class RoleOption(BaseModel):
    value: str
    name: str


class DictionariesOut(BaseModel):
    asset_status: list[DictOption]
    borrow_status: list[DictOption]
    inventory_task_status: list[DictOption]
    inventory_result: list[DictOption]
    inspection_type: list[DictOption]
    inspection_status: list[DictOption]
    inspection_result: list[DictOption]
    reservation_status: list[DictOption]
    domain: list[DictOption]
    data_scope: list[DictOption]
    org_type: list[DictOption]
    role: list[RoleOption]
    permissions: dict[str, list[str]]
