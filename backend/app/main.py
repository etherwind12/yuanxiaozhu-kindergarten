"""应用入口：装配路由、中间件与启动初始化。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.db.init_db import init_db

# 导入各模块 ORM 模型，确保 Base.metadata 注册完整后再建表
from app.modules.assets import models as _assets_models  # noqa: F401
from app.modules.auth import models as _auth_models  # noqa: F401
from app.modules.borrow import models as _borrow_models  # noqa: F401
from app.modules.inspection import models as _inspection_models  # noqa: F401
from app.modules.inventory import models as _inventory_models  # noqa: F401
from app.modules.org import models as _org_models  # noqa: F401
from app.modules.report import models as _report_models  # noqa: F401
from app.modules.teaching import models as _teaching_models  # noqa: F401

from app.modules.assets.router import router as assets_router
from app.modules.assistant.router import router as assistant_router
from app.modules.auth.router import router as auth_router
from app.modules.borrow.router import router as borrow_router
from app.modules.inspection.router import router as inspection_router
from app.modules.inventory.router import router as inventory_router
from app.modules.meta.router import router as meta_router
from app.modules.org.router import router as org_router
from app.modules.report.router import router as report_router
from app.modules.teaching.router import router as teaching_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    init_db()
    yield


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=f"{settings.API_PREFIX}/auth", tags=["认证与用户"])
app.include_router(org_router, prefix=f"{settings.API_PREFIX}/org", tags=["组织与数据域"])
app.include_router(assets_router, prefix=f"{settings.API_PREFIX}/assets", tags=["资产"])
app.include_router(borrow_router, prefix=f"{settings.API_PREFIX}/borrow", tags=["借还"])
app.include_router(inventory_router, prefix=f"{settings.API_PREFIX}/inventory", tags=["盘点"])
app.include_router(inspection_router, prefix=f"{settings.API_PREFIX}/inspection", tags=["巡检"])
app.include_router(teaching_router, prefix=f"{settings.API_PREFIX}/teaching", tags=["教学联动"])
app.include_router(report_router, prefix=f"{settings.API_PREFIX}/report", tags=["报表"])
app.include_router(assistant_router, prefix=f"{settings.API_PREFIX}/assistant", tags=["AI 助手"])
app.include_router(meta_router, prefix=f"{settings.API_PREFIX}/meta", tags=["系统字典"])


@app.get("/api/health", tags=["系统"], summary="健康检查")
def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME}
