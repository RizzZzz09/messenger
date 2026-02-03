import re
import uuid
from datetime import datetime, timedelta, timezone

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
    InvalidUsernameError,
    UsernameAlreadyExistsError,
    UsernameContainsWhitespaceError,
)


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    """Регистрирует пользователя.

    Args:
        db: SQLAlchemy-сессия, предоставляемая зависимостью get_db().
        payload: Данные для создания пользователя.

    Returns:
        Новый пользователь.

    Raises:
        UsernameContainsWhitespaceError: Если в имени пользователя есть пробелы.
        EmailAlreadyExistsError: Если пользователь с такой электронной почтой уже зарегистрирован.
        UsernameAlreadyExistsError: Если пользователь с таким именем уже зарегистрирован.
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
    """Авторизация пользователя.

    Args:
        db: SQLAlchemy-сессия, предоставляемая зависимостью get_db().
        login: Логин пользователя.
        password: Пароль пользователя.

    Returns:
        tuple(access_token, refresh_token)
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
