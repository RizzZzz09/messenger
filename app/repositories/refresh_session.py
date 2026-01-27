from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_session import RefreshSession


class RefreshSessionRepository:
    """Репозиторий для работы с refresh-сессиями (хранение хэшей refresh-токенов)."""

    def __init__(self, db: AsyncSession):
        """Создает репозиторий refresh-сессий.

        Args:
            db: SQLAlchemy-сессия, предоставляемая зависимостью get_db().
        """
        self._db = db

    async def create(self, refresh_session: RefreshSession) -> RefreshSession:
        """Сохраняет refresh-сессию в базе данных.

        Args:
            refresh_session: Объект refresh-сессии для сохранения.

        Returns:
            Сохраненная refresh-сессия с обновленными полями (например, created_at).
        """
        self._db.add(refresh_session)
        await self._db.commit()
        await self._db.refresh(refresh_session)
        return refresh_session

    async def get_by_id(self, session_id: UUID) -> RefreshSession | None:
        """Возвращает refresh-сессию по ее UUID.

        Args:
            session_id: UUID записи refresh-сессии.

        Returns:
            Refresh-сессия, если найдена, иначе None.
        """
        stmt = select(RefreshSession).where(RefreshSession.id == session_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, session_id: UUID) -> bool:
        """Отзывает refresh-сессию (ставит revoked_at = now()).

        Args:
            session_id: UUID записи refresh-сессии.
        """
        stmt = (
            update(RefreshSession)
            .where(RefreshSession.id == session_id)
            .where(RefreshSession.revoked_at.is_(None))
            .values(revoked_at=func.now())
        )
        result = cast(CursorResult[Any], await self._db.execute(stmt))
        await self._db.commit()
        return (result.rowcount or 0) > 0
