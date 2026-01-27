from hashlib import sha256

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from authx import AuthX

from app.core.config import auth_config

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Хеширует переданный пароль.

    Args:
        password: Исходный пароль.

    Returns:
        Хешированный пароль.
    """
    hashed: str = ph.hash(password)
    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль.

    Args:
        plain_password: Исходный текст пароля.
        hashed_password: Хешированный пароль.

    Returns:
        True если пароль верен, иначе False.
    """
    try:
        result: bool = ph.verify(hashed_password, plain_password)
        return result
    except VerificationError:
        return False


def hash_refresh_token(refresh_token: str) -> str:
    """Хеширует переданный refresh token.

    Args:
        refresh_token: Исходный refresh token.

    Returns:
        Хешированный refresh token.
    """
    return sha256(refresh_token.encode()).hexdigest()


auth = AuthX(config=auth_config)
