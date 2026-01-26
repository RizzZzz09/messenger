from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest
from app.services.errors import (
    EmailAlreadyExistsError,
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
