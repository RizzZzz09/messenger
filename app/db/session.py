from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)

async_session_factory = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Создает асинхронный генератор базы данных.

    Создает новую AsyncSession на время одного запроса и гарантирует
    корректное закрытие соединения после завершения работы.

    Используется как dependency в FastAPI.
    """
    async with async_session_factory() as session:
        yield session
