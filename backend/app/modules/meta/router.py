"""元数据（字典）模块 - 路由。"""

from fastapi import APIRouter, Depends

from app.common.deps import get_current_user
from app.modules.auth.models import User
from app.modules.meta import service
from app.modules.meta.schemas import DictionariesOut

router = APIRouter()


@router.get(
    "/dictionaries",
    response_model=DictionariesOut,
    summary="系统字典（状态 / 类型 / 领域 / 数据域 / 组织类型 / 角色权限）",
)
def get_dictionaries(_: User = Depends(get_current_user)) -> DictionariesOut:
    return DictionariesOut(**service.build())
