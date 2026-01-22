from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Репозиторий для работы с пользователями (User)."""

    def __init__(self, db: AsyncSession):
        """Создает репозиторий пользователей.

        Args:
            db: SQLAlchemy-сессия, предоставляемая зависимостью get_db()
        """
        self._db = db

    async def create(self, user: User) -> User:
        """Создает пользователя.

        Args:
            user: Пользователь для сохранения.

        Returns:
            Сохраненный пользователь с обновленными полями.
        """
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        """Возвращает пользователя по электронной почте.

        Args:
            email: Электронная почта пользователя.

        Returns:
            Пользователь, если найден, иначе None.
        """
        stmt = select(User).where(User.email == email)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Возвращает пользователя по имени пользователя.

        Args:
            username: Имя пользователя.

        Returns:
            Пользователь, если найден, иначе None.
        """
        stmt = select(User).where(User.username == username)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
