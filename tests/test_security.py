import pytest

from app.core.security import hash_password, hash_refresh_token, verify_password


# --- Корректность работы функций хеширования пароля. ---
@pytest.mark.parametrize(
    "password",
    [
        "test_password",
        "my_password",
        "123456789",
        "my_test_password123",
        "@my_test12344444Password",
    ],
)
def test_hash_password(password: str) -> None:
    """Пароль успешно хешируется и корректно верифицируется."""
    password_hash = hash_password(password)

    assert password_hash
    assert password_hash != password
    assert verify_password(password, password_hash) is True


@pytest.mark.parametrize(
    "password",
    [
        "test_password",
        "my_password",
        "123456789",
        "my_test_password123",
        "@my_test12344444Password",
    ],
)
def test_one_password_two_hashes(password: str) -> None:
    """Один и тот же пароль при повторном хешировании имеет разный хеш.

    Оба варианта хеширования корректно верифицируются.
    """
    password_hash_first = hash_password(password)
    password_hash_second = hash_password(password)

    assert password_hash_first
    assert password_hash_second
    assert password_hash_first != password_hash_second
    assert verify_password(password, password_hash_first) is True


@pytest.mark.parametrize(
    "password",
    [
        "test_password",
        "my_password",
        "123456789",
        "my_test_password123",
        "@my_test12344444Password",
    ],
)
def test_hash_password_return_type(password: str) -> None:
    """Функия hash_password возвращает захешированный пароль типа str."""
    password_hash = hash_password(password)

    assert password_hash
    assert isinstance(password_hash, str)


# --- Корректность работы функций хеширования refresh token. ---
@pytest.mark.parametrize(
    "refresh_token",
    [
        "refresh_token_first",
        "refresh_token1",
        "refresh_token_2",
        "random_refresh_token",
    ],
)
def test_hash_refresh_token(refresh_token: str) -> None:
    """Refresh token успешно хешируется."""
    refresh_token_hash = hash_refresh_token(refresh_token)

    assert refresh_token_hash
    assert refresh_token_hash != refresh_token


@pytest.mark.parametrize(
    "refresh_token",
    [
        "refresh_token_first",
        "refresh_token1",
        "refresh_token_2",
        "random_refresh_token",
    ],
)
def test_one_refresh_token_one_hash(refresh_token: str) -> None:
    """Один и тот же refresh token имеет одинаковый хеш так как он детерминированный."""
    refresh_token_hash_first = hash_refresh_token(refresh_token)
    refresh_token_hash_second = hash_refresh_token(refresh_token)

    assert refresh_token_hash_first
    assert refresh_token_hash_second
    assert refresh_token_hash_first == refresh_token_hash_second


@pytest.mark.parametrize(
    "refresh_token",
    [
        "refresh_token_first",
        "refresh_token1",
        "refresh_token_2",
        "random_refresh_token",
    ],
)
def test_other_refresh_token_has_other_hash(refresh_token: str) -> None:
    """Разные refresh token имеют разные хэши."""
    other_refresh_token_hash = hash_refresh_token("other_refresh_token")
    refresh_token_hash = hash_refresh_token(refresh_token)

    assert other_refresh_token_hash
    assert refresh_token_hash
    assert other_refresh_token_hash != refresh_token_hash


@pytest.mark.parametrize(
    "refresh_token",
    [
        "refresh_token_first",
        "refresh_token1",
        "refresh_token_2",
        "random_refresh_token",
    ],
)
def test_hash_refresh_token_return_type(refresh_token: str) -> None:
    """Функция hash_refresh_token возвращает захешированный refresh token типа str."""
    refresh_token_hash = hash_refresh_token(refresh_token)

    assert refresh_token_hash
    assert isinstance(refresh_token_hash, str)
