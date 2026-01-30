import os
from collections.abc import AsyncGenerator, Generator

import pytest
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.session import get_db
from app.main import app

load_dotenv(".env.test")


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Возвращает URL тестовой базы данных из переменной окружения TEST_DATABASE_URL."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "TEST_DATABASE_URL not set. Check .env.test, example:\n"
            "TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/messenger_test"
        )
    return url


@pytest.fixture(scope="session")
def engine(test_db_url: str) -> AsyncEngine:
    """Создает AsyncEngine для тестовой базы данных.

    Args:
        test_db_url: URL тестовой базы данных.
    """
    return create_async_engine(test_db_url, future=True)


@pytest.fixture
async def connection(engine: AsyncEngine) -> AsyncGenerator[AsyncConnection, None]:
    """Предоставляет одно DB-соединение (AsyncConnection) на время одного теста.

    Args:
        engine: AsyncEngine тестовой базы данных.

    Yields:
        Открытое соединение AsyncConnection.
    """
    async with engine.connect() as connection:
        yield connection


@pytest.fixture
async def db_session(connection: AsyncConnection) -> AsyncGenerator[AsyncSession, None]:
    """Предоставляет ORM-сессию (AsyncSession) на время одного теста и откатывает изменения.

    Args:
        connection: DB-соединение (AsyncConnection) для текущего теста.

    Yields:
        ORM-сессия AsyncSession, которую будут использовать роуты через Depends(get_db).
    """
    transaction = await connection.begin()

    async_session_factory = async_sessionmaker(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()


@pytest.fixture
def override_get_db(db_session: AsyncSession) -> Generator[None, None, None]:
    """Переопределяет зависимость get_db так, чтобы роуты использовали тестовую ORM-сессию.

    Args:
        db_session: ORM-сессия AsyncSession.

    Yields:
        Ничего не возвращает. Используется как "включить/выключить" override.
    """

    async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    try:
        yield
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
async def client(override_get_db: None) -> AsyncGenerator[AsyncClient, None]:
    """HTTP-клиент для запросов к FastAPI приложению в памяти (без uvicorn).

    Args:
        override_get_db: Фикстура, которая гарантирует, что get_db подменён на тестовую сессию.

    Yields:
        AsyncClient, которым можно делать запросы к API.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
