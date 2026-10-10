"""AI 助手 - 路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.deps import get_current_user
from app.core.database import get_db
from app.modules.assistant import service
from app.modules.assistant.schemas import ChatIn, ChatOut
from app.modules.auth.models import User

router = APIRouter()


@router.post("/chat", response_model=ChatOut, summary="AI 资产助手对话")
def chat(
    payload: ChatIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> ChatOut:
    return ChatOut(**service.chat(db, user, payload.message))
