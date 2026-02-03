import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import RegisterResponse


@pytest.mark.asyncio
async def test_successful_user_registration(client: AsyncClient) -> None:
    """Пользователь успешно зарегистрировался."""

    payload = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "test_password",
    }

    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()

    assert RegisterResponse.model_validate(data)
    assert data["email"] == payload["email"]
    assert data["username"] == payload["username"]
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_username_contains_whitespace_error(client: AsyncClient) -> None:
    """Имя пользователя содержит пробелы. Ошибка при регистрации"""
    payload = {
        "email": "test_email@gmail.com",
        "username": "test username",
        "password": "test_password",
    }

    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422

    data = response.json()

    assert "detail" in data
    assert data["detail"] == "username_contains_whitespace"


@pytest.mark.asyncio
async def test_email_already_exists(client: AsyncClient) -> None:
    """Пользователь с такой электронной почтой уже существует. Ошибка при регистрации."""
    first_payload = {
        "email": "test_email@gmail.com",
        "username": "test_first_username",
        "password": "test_first_password",
    }

    second_payload = {
        "email": "test_email@gmail.com",
        "username": "test_second_username",
        "password": "test_second_password",
    }

    response_first = await client.post("/auth/register", json=first_payload)
    assert response_first.status_code == 201

    response_second = await client.post("/auth/register", json=second_payload)
    assert response_second.status_code == 409

    data = response_second.json()

    assert "detail" in data
    assert data["detail"] == "email_already_exists"


@pytest.mark.asyncio
async def test_username_already_exists(client: AsyncClient) -> None:
    """Пользователь с таким именем пользователя уже существует. Ошибка при регистрации."""
    first_payload = {
        "email": "test_first_email@gmail.com",
        "username": "test_username",
        "password": "test_first_password",
    }

    second_payload = {
        "email": "test_second_email@gmail.com",
        "username": "test_username",
        "password": "test_second_password",
    }

    response_first = await client.post("/auth/register", json=first_payload)
    assert response_first.status_code == 201

    response_second = await client.post("/auth/register", json=second_payload)
    assert response_second.status_code == 409

    data = response_second.json()

    assert "detail" in data
    assert data["detail"] == "username_already_exists"


@pytest.mark.asyncio
async def test_incorrect_email_format(client: AsyncClient) -> None:
    """Некорректный формат электронной почты."""
    payload = {
        "email": "test_email_gmail.com",
        "username": "test_username",
        "password": "test_password",
    }

    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422

    data = response.json()

    assert "detail" in data
    assert data["detail"][0]["loc"] == ["body", "email"]
    assert data["detail"][0]["type"] == "value_error"


@pytest.mark.asyncio
async def test_short_password(client: AsyncClient) -> None:
    """Слишком короткий пароль."""
    payload = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "my_pass",
    }

    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422

    data = response.json()

    assert "detail" in data
    assert data["detail"][0]["loc"] == ["body", "password"]
    assert data["detail"][0]["type"] == "string_too_short"


@pytest.mark.asyncio
async def test_extra_fields(client: AsyncClient) -> None:
    """Лишние поля при регистрации"""
    payload = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "test_password",
        "age": 3,
    }

    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422

    data = response.json()

    assert "detail" in data
    assert data["detail"][0]["loc"] == ["body", "age"]
    assert data["detail"][0]["type"] == "extra_forbidden"


@pytest.mark.asyncio
async def test_hash_password_in_database(client: AsyncClient, db_session: AsyncSession) -> None:
    """После регистрации в базе данных хранится захешированный пароль, а не исходный."""
    payload = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "test_password",
    }

    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 201

    stmt = select(User).where(User.email == payload["email"])
    result = await db_session.execute(stmt)
    user = result.scalar_one()

    assert user.password_hash is not None
    assert user.password_hash != payload["password"]
