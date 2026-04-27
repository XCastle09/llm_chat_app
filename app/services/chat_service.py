from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Chat, Message

class ChatService:
    @staticmethod
    async def create_chat(user_id: int, title: str, db: AsyncSession) -> Chat:
        chat = Chat(user_id=user_id, title=title)
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        return chat

    @staticmethod
    async def get_user_chats(user_id: int, db: AsyncSession):
        result = await db.execute(select(Chat).where(Chat.user_id == user_id).order_by(Chat.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_chat_messages(chat_id: int, user_id: int, db: AsyncSession):
        chat = await db.get(Chat, chat_id)
        if not chat or chat.user_id != user_id:
            return None
        result = await db.execute(select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at))
        return result.scalars().all()