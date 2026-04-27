import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from app.models import Base

async def create_tables():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())