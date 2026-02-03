import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_session import RefreshSession
from app.models.user import User
from app.schemas.auth import LoginResponse


@pytest.mark.asyncio
async def test_successful_login_by_username(client: AsyncClient) -> None:
    """Успешная авторизация по имени пользователя."""
    payload_reg = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "test_password",
    }

    payload_log = {
        "login": "test_username",
        "password": "test_password",
    }

    response_reg = await client.post("/auth/register", json=payload_reg)
    assert response_reg.status_code == 201

    response_log = await client.post("/auth/login", json=payload_log)
    assert response_log.status_code == 200

    data = response_log.json()
    set_cookie = response_log.headers.get("set-cookie", "")

    LoginResponse.model_validate(data)

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    assert "refresh" in set_cookie.lower()
    assert "httponly" in set_cookie.lower()


@pytest.mark.asyncio
async def test_successful_login_by_email(client: AsyncClient) -> None:
    """Успешная авторизация по электронной почте."""
    payload_reg = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "test_password",
    }

    payload_log = {
        "login": "test_email@gmail.com",
        "password": "test_password",
    }

    response_reg = await client.post("/auth/register", json=payload_reg)
    assert response_reg.status_code == 201

    response_log = await client.post("/auth/login", json=payload_log)
    assert response_log.status_code == 200

    data = response_log.json()
    set_cookie = response_log.headers.get("set-cookie", "")
    LoginResponse.model_validate(data)

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    assert "refresh" in set_cookie.lower()
    assert "httponly" in set_cookie.lower()


@pytest.mark.asyncio
async def test_invalid_password(client: AsyncClient) -> None:
    """Пользователь ввел неверный пароль."""
    payload_reg = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "test_password",
    }

    payload_log = {
        "login": "test_email@gmail.com",
        "password": "test_my_password",
    }

    response_reg = await client.post("/auth/register", json=payload_reg)
    assert response_reg.status_code == 201

    response_log = await client.post("/auth/login", json=payload_log)
    assert response_log.status_code == 401

    data = response_log.json()

    assert "detail" in data
    assert data["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_no_user_by_email(client: AsyncClient) -> None:
    """Пользователя с такой электронной почтой не существует."""
    payload_reg = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "test_password",
    }

    payload_log = {
        "login": "test_email@mail.com",
        "password": "test_password",
    }

    response_reg = await client.post("/auth/register", json=payload_reg)
    assert response_reg.status_code == 201

    response_log = await client.post("/auth/login", json=payload_log)
    assert response_log.status_code == 401

    data = response_log.json()

    assert "detail" in data
    assert data["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_no_user_by_username(client: AsyncClient) -> None:
    """Пользователя с таким именем пользователя не существует."""
    payload_reg = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "test_password",
    }

    payload_log = {
        "login": "test_my_username",
        "password": "test_password",
    }

    response_reg = await client.post("/auth/register", json=payload_reg)
    assert response_reg.status_code == 201

    response_log = await client.post("/auth/login", json=payload_log)
    assert response_log.status_code == 401

    data = response_log.json()

    assert "detail" in data
    assert data["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_invalid_format_email(client: AsyncClient) -> None:
    """Пользователь ввел невалидный формат электронной почты."""
    payload_reg = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "test_password",
    }

    payload_log = {
        "login": "test_email_gmail.com",
        "password": "test_password",
    }

    response_reg = await client.post("/auth/register", json=payload_reg)
    assert response_reg.status_code == 201

    response_log = await client.post("/auth/login", json=payload_log)
    assert response_log.status_code == 401

    data = response_log.json()

    assert "detail" in data
    assert data["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_invalid_format_username(client: AsyncClient) -> None:
    """Пользователь ввел невалидный формат имени пользователя."""
    payload_reg = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "test_password",
    }

    payload_log = {
        "login": "test username",
        "password": "test_password",
    }

    response_reg = await client.post("/auth/register", json=payload_reg)
    assert response_reg.status_code == 201

    response_log = await client.post("/auth/login", json=payload_log)
    assert response_log.status_code == 401

    data = response_log.json()

    assert "detail" in data
    assert data["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_refresh_session_created_by_database(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """В базе данных хранится только захешированный refresh_token"""
    payload_reg = {
        "email": "test_email@gmail.com",
        "username": "test_username",
        "password": "test_password",
    }

    payload_log = {
        "login": "test_username",
        "password": "test_password",
    }

    response_reg = await client.post("/auth/register", json=payload_reg)
    assert response_reg.status_code == 201

    response_log = await client.post("/auth/login", json=payload_log)
    assert response_log.status_code == 200

    user_stmt = select(User).where(User.email == payload_reg["email"])
    user_result = await db_session.execute(user_stmt)
    user = user_result.scalar_one()

    rs_stmt = select(RefreshSession).where(RefreshSession.user_id == user.id)
    rs_result = await db_session.execute(rs_stmt)
    refresh_session = rs_result.scalar_one()

    set_cookie = response_log.headers.get("set-cookie", "")
    refresh_token = set_cookie.split("=", 1)[1].split(";", 1)[0]

    assert "httponly" in set_cookie.lower()

    assert refresh_session.user_id == user.id
    assert refresh_session.refresh_token_hash is not None
    assert refresh_session.refresh_token_hash != refresh_token
