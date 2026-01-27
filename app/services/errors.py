from typing import ClassVar


# --- Группировка 1: Ошибки при работе с пользователем ---
class UserError(Exception):
    """Базовая ошибка при работе с пользователем."""

    reason: ClassVar[str]

    def __init__(self, message: str) -> None:
        super().__init__(message)


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


# --- Группировка 2: Ошибки уровня сервиса ---
class ServiceError(Exception):
    """Базовая ошибка при работе с сервисом."""

    reason: ClassVar[str]

    def __init__(self, message: str) -> None:
        super().__init__(message)


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
