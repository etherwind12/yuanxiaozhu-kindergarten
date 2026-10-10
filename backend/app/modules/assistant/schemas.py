"""AI 助手 - 数据传输对象。"""

from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=200)


class KV(BaseModel):
    label: str
    value: str | int


class ChartItem(BaseModel):
    name: str
    count: int


class TableOut(BaseModel):
    columns: list[str] = []
    rows: list[list[str]] = []


class ChatOut(BaseModel):
    reply: str
    mode: str = "rules"
    data: list[KV] = []
    chart: list[ChartItem] = []
    table: TableOut | None = None
    examples: list[str] = []
