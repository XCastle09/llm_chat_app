from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import User, Chat
from ..schemas import MessageCreate
from ..dependencies import get_current_user
from ..services.llm_chat_service import LLMChatService

router = APIRouter(prefix="/ask", tags=["ask"])

@router.post("/")
async def ask_question(
    chat_id: int = Query(...),
    message_data: MessageCreate = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Проверка принадлежности чата пользователю
    chat = await db.get(Chat, chat_id)
    if not chat or chat.user_id != user.id:
        raise HTTPException(403, "Not your chat")
    answer = await LLMChatService.ask_and_save(chat_id, message_data.message, db)
    return {"answer": answer}