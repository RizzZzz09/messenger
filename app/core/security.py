from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

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
