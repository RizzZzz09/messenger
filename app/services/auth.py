import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Protocol, TypeAlias

from authx import TokenPayload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import auth, hash_password, hash_refresh_token, verify_password
from app.models.refresh_session import RefreshSession
from app.models.user import User
from app.repositories.refresh_session import RefreshSessionRepository
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest
from app.services.errors import (
    EmailAlreadyExistsError,
    InvalidPasswordError,
    InvalidRefreshTokenError,
    InvalidUsernameError,
    RefreshSessionMismatchError,
    RefreshSessionNotFoundError,
    UsernameAlreadyExistsError,
    UsernameContainsWhitespaceError,
)


class RefreshTokenLike(Protocol):
    token: str


RefreshTokenRaw: TypeAlias = str | RefreshTokenLike


def _normalize_refresh_token(refresh_token_raw: RefreshTokenRaw) -> str:
    """Нормализует refresh-токен до строкового представления.

    Args:
        refresh_token_raw: Refresh-токен в виде строки или объекта, содержащего атрибут `token`.

    Returns:
        Строковое представление refresh-токена.
    """
    return (
        refresh_token_raw.token if hasattr(refresh_token_raw, "token") else str(refresh_token_raw)
    )


async def _validate_refresh_session(
    db: AsyncSession, refresh_token_raw: RefreshTokenRaw, payload: TokenPayload
) -> RefreshSession:
    """Валидирует refresh-токен и возвращает связанную refresh-сессию.

    Проверяет существование активной refresh-сессии, срок её действия и
    соответствие пользователя данным из JWT (uid).

    Args:
        db: Асинхронная сессия базы данных.
        refresh_token_raw: Исходный refresh-токен (не хэшированный).
        payload: Payload валидированного refresh JWT.

    Returns:
        Активная refresh-сессия.

    Raises:
        InvalidRefreshTokenError: Если refresh-токен отсутствует или невалиден.
        RefreshSessionNotFoundError: Если активная refresh-сессия не найдена.
        RefreshSessionMismatchError: Если uid токена не соответствует сессии.
    """
    # Проверка наличия refresh_token_raw
    if not refresh_token_raw:
        raise InvalidRefreshTokenError()

    refresh_token_str = _normalize_refresh_token(refresh_token_raw)
    token_hash = hash_refresh_token(refresh_token_str)
    session_repo = RefreshSessionRepository(db)
    session = await session_repo.get_active_by_hash(token_hash)

    # Проверка существования такой сессии
    if not session:
        raise RefreshSessionNotFoundError()

    uid = payload.sub

    # Проверка связи uid и user_id данной сессии
    if uid != str(session.user_id):
        raise RefreshSessionMismatchError()

    return session


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    """Регистрирует нового пользователя в системе.

    Выполняет бизнес-валидацию данных, проверяет уникальность email и username,
    хеширует пароль и сохраняет пользователя в базе данных.

    Args:
        db: Асинхронная сессия базы данных.
        payload: Данные для регистрации пользователя.

    Returns:
        Созданный пользователь.

    Raises:
        UsernameContainsWhitespaceError: Если username содержит пробелы.
        EmailAlreadyExistsError: Если пользователь с таким email уже существует.
        UsernameAlreadyExistsError: Если пользователь с таким username уже существует.
    """
    # Проверка на пробелы в имени пользователя
    if " " in payload.username:
        raise UsernameContainsWhitespaceError(payload.username)

    # Проверка уникальности пользовательских данных
    user_repo = UserRepository(db)

    # Уникальность электронной почты
    email = str(payload.email)

    if await user_repo.get_by_email(email):
        raise EmailAlreadyExistsError(email)

    # Уникальность имени пользователя
    if await user_repo.get_by_username(payload.username):
        raise UsernameAlreadyExistsError(payload.username)

    # Хеширование пароля
    password_hash = hash_password(payload.password)

    # Создание пользователя
    user = User(
        email=email,
        username=payload.username,
        password_hash=password_hash,
    )

    try:
        return await user_repo.create(user)
    except IntegrityError as error:
        constraint = getattr(error.orig, "constraint_name", None)
        if constraint == "uq_users_email":
            raise EmailAlreadyExistsError(email)
        if constraint == "uq_users_username":
            raise UsernameAlreadyExistsError(payload.username)
        raise


async def login_user(db: AsyncSession, login: str, password: str) -> tuple[str, str]:
    """Аутентифицирует пользователя и создаёт новую refresh-сессию.

    Выполняет вход по email или username, проверяет пароль, создаёт access
    и refresh JWT-токены и сохраняет refresh-сессию в базе данных.

    Args:
        db: Асинхронная сессия базы данных.
        login: Email или username пользователя.
        password: Пароль пользователя.

    Returns:
        Кортеж из access-токена и refresh-токена.

    Raises:
        InvalidUsernameError: Если пользователь не найден.
        InvalidPasswordError: Если пароль неверен.
    """
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    login_pattern = r"^[a-zA-Z0-9_]{3,20}$"

    user_repo = UserRepository(db)

    if re.fullmatch(email_pattern, login):
        user = await user_repo.get_by_email(login)
    elif re.fullmatch(login_pattern, login):
        user = await user_repo.get_by_username(login)
    else:
        raise InvalidUsernameError()

    # Проверка существует ли пользователь по email или login
    if not user:
        raise InvalidUsernameError()

    # Проверка корректности пароля.
    if not verify_password(password, user.password_hash):
        raise InvalidPasswordError()

    session_id = uuid.uuid4()
    access_token = auth.create_access_token(uid=str(user.id))
    refresh_token = auth.create_refresh_token(uid=str(user.id), sid=str(session_id))
    refresh_token_hash = hash_refresh_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRES)

    refresh_session = RefreshSession(
        id=session_id,
        user_id=user.id,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at,
        revoked_at=None,
    )

    session_repo = RefreshSessionRepository(db)
    await session_repo.create(refresh_session)

    return access_token, refresh_token


async def refresh_tokens(
    db: AsyncSession, refresh_token_raw: RefreshTokenRaw, payload: TokenPayload
) -> tuple[str, str]:
    """Обновляет access-токен с ротацией refresh-сессии.

    Валидирует текущую refresh-сессию, отзывает её и создаёт новую
    refresh-сессию с новым refresh-токеном.

    Args:
        db: Асинхронная сессия базы данных.
        refresh_token_raw: Исходный refresh-токен (не хэшированный).
        payload: Payload валидированного refresh JWT.

    Returns:
        Кортеж из нового access-токена и нового refresh-токена.

    Raises:
        InvalidRefreshTokenError: Если refresh-токен невалиден.
        RefreshSessionNotFoundError: Если refresh-сессия не найдена.
        RefreshSessionMismatchError: Если данные токена не соответствуют сессии.
    """
    old_session = await _validate_refresh_session(db, refresh_token_raw, payload)
    session_repo = RefreshSessionRepository(db)
    await session_repo.revoke(old_session.id)

    new_session_id = uuid.uuid4()
    access_token = auth.create_access_token(uid=str(old_session.user_id))
    new_refresh_token = auth.create_refresh_token(
        uid=str(old_session.user_id), sid=str(new_session_id)
    )
    new_hash = hash_refresh_token(new_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRES)

    new_session = RefreshSession(
        id=new_session_id,
        user_id=old_session.user_id,
        refresh_token_hash=new_hash,
        expires_at=expires_at,
        revoked_at=None,
    )

    await session_repo.create(new_session)
    return access_token, new_refresh_token


async def logout_user_idempotent(db: AsyncSession, refresh_token_raw: RefreshTokenRaw) -> None:
    """Идемпотентно завершает refresh-сессию пользователя.

    Пытается отозвать активную refresh-сессию, связанную с переданным
    refresh-токеном. Если сессия не найдена или уже отозвана, функция
    корректно завершается без ошибок.

    Args:
        db: Асинхронная сессия базы данных.
        refresh_token_raw: Исходный refresh-токен из HttpOnly cookie.
    """
    refresh_token_str = _normalize_refresh_token(refresh_token_raw)
    token_hash = hash_refresh_token(refresh_token_str)

    session_repo = RefreshSessionRepository(db)
    session = await session_repo.get_active_by_hash(token_hash)

    if not session:
        return

    await session_repo.revoke(session.id)
