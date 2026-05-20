from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models import User
from ..schemas import ChatCreate
from ..dependencies import get_current_user
from ..services.chat_service import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("/")
async def create_chat(chat_data: ChatCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ChatService.create_chat(user.id, chat_data.title, db)

@router.get("/")
async def list_chats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ChatService.get_user_chats(user.id, db)

@router.get("/{chat_id}/messages")
async def get_messages(chat_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    messages = await ChatService.get_chat_messages(chat_id, user.id, db)
    if messages is None:
        raise HTTPException(404, "Chat not found")
    return messages