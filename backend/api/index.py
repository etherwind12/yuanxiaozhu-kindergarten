"""Vercel 无服务器函数入口。

Vercel 会把 api/index.py 映射为 /api 路由，函数内应用仍按请求的原始路径匹配，
因此后端既有的 /api 前缀路由无需改动。
"""

from app.main import app  # noqa: F401