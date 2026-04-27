from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Message
from ..llm_service import generate_response

class LLMChatService:
    @staticmethod
    async def ask_and_save(chat_id: int, user_message: str, db: AsyncSession) -> str:
        # Сохраняем сообщение пользователя
        user_msg = Message(chat_id=chat_id, role="user", content=user_message)
        db.add(user_msg)
        await db.flush()
        
        # Получаем последние 5 сообщений для контекста
        result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(5)
        )
        history = list(result.scalars().all())
        history.reverse()  # от старых к новым
        
        # Формируем промпт с историей
        prompt = ""
        for msg in history:
            if msg.role == "user":
                prompt += f"Human: {msg.content}\n"
            else:
                prompt += f"Assistant: {msg.content}\n"
        prompt += f"Human: {user_message}\nAssistant: "
        
        # Генерируем ответ
        answer = generate_response(prompt)
        
        # Если ответ пустой, даём стандартный
        if not answer or answer.strip() == "":
            answer = "I'm not sure how to answer that. Could you rephrase?"
        
        assistant_msg = Message(chat_id=chat_id, role="assistant", content=answer)
        db.add(assistant_msg)
        await db.commit()
        return answer