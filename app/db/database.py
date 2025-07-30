from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession)


async def get_session() -> AsyncGenerator:
    async with async_session() as session:
        yield session
