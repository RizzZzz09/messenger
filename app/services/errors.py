from typing import ClassVar


# =============================================================================
# Базовые типы ошибок
# =============================================================================
class UserError(Exception):
    """Базовая ошибка при работе с пользователем."""

    reason: ClassVar[str]

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ServiceError(Exception):
    """Базовая ошибка при работе с сервисом."""

    reason: ClassVar[str]

    def __init__(self, message: str) -> None:
        super().__init__(message)


# =============================================================================
# Ошибки домена пользователя (регистрация / данные пользователя)
# =============================================================================
class UsernameContainsWhitespaceError(UserError):
    """Имя пользователя содержит пробелы."""

    reason: ClassVar[str] = "username_contains_whitespace"

    def __init__(self, username: str) -> None:
        super().__init__(f'Username: "{username}" contains whitespace')


class EmailAlreadyExistsError(UserError):
    """Пользователь с такой электронной почтой уже существует."""

    reason: ClassVar[str] = "email_already_exists"

    def __init__(self, email: str) -> None:
        super().__init__(f'Email: "{email}" already exists')


class UsernameAlreadyExistsError(UserError):
    """Имя пользователя уже существует."""

    reason: ClassVar[str] = "username_already_exists"

    def __init__(self, username: str) -> None:
        super().__init__(f'Username: "{username}" already exists')


# =============================================================================
# Ошибки аутентификации и учетных данных
# =============================================================================
class InvalidUsernameError(ServiceError):
    """Пользователя с таким именем не существует."""

    reason: ClassVar[str] = "invalid_username"

    def __init__(self) -> None:
        super().__init__("Invalid credentials")


class InvalidPasswordError(ServiceError):
    """Неверный пароль."""

    reason: ClassVar[str] = "invalid_password"

    def __init__(self) -> None:
        super().__init__("Invalid credentials")


class InvalidRefreshTokenError(ServiceError):
    """Refresh token не валиден как токен."""

    reason: ClassVar[str] = "invalid_refresh_token"

    def __init__(self) -> None:
        super().__init__("Invalid refresh token")


# =============================================================================
# Ошибки refresh-сессий (состояние БД / несоответствия)
# =============================================================================
class RefreshSessionNotFoundError(ServiceError):
    """Refresh сессии не существует."""

    reason: ClassVar[str] = "refresh_session_not_found"

    def __init__(self) -> None:
        super().__init__("Refresh session not found")


class RefreshSessionMismatchError(ServiceError):
    """Uid/sid mismatch между токеном и сессией."""

    reason: ClassVar[str] = "refresh_session_mismatch"

    def __init__(self) -> None:
        super().__init__("Refresh session mismatch")
