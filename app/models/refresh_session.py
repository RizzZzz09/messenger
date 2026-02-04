import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class RefreshSession(Base):
    """ORM-модель JWT Refresh Token."""

    __tablename__ = "refresh_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID записи refresh-сессии",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK на users.id — владелец refresh-сессии",
    )

    refresh_token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Хэш refresh-токена (не хранить токен в чистом виде)",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата истечения refresh-сессии"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания refresh-сессии",
    )

    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата отзыва refresh-сессии (если отозвана)",
    )

    user: Mapped["User"] = relationship(
        back_populates="refresh_sessions",
    )
