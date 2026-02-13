from authx import TokenPayload
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import auth
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth import (
    RefreshTokenRaw,
    login_user,
    logout_user_idempotent,
    refresh_tokens,
    register_user,
)
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

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    summary="Регистрация пользователя",
    description=(
        "Создаёт нового пользователя.\n\n"
        "Правила:\n"
        "- email и username уникальны\n"
        "- username не содержит пробелов\n"
        "- пароль сохраняется только в виде хэша"
    ),
    responses={
        201: {"description": "Пользователь зарегистрирован."},
        409: {"description": "Email или username уже заняты."},
        422: {"description": "Ошибка валидации входных данных."},
    },
)
async def register(
    payload: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> RegisterResponse:
    try:
        user = await register_user(db, payload)
    except UsernameContainsWhitespaceError as error:
        raise HTTPException(status_code=422, detail=error.reason) from error
    except (EmailAlreadyExistsError, UsernameAlreadyExistsError) as error:
        raise HTTPException(status_code=409, detail=error.reason) from error
    else:
        return RegisterResponse.model_validate(user)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Вход в систему",
    description=(
        "Аутентификация по email или username.\n\n"
        "Результат:\n"
        "- access-токен возвращается в теле ответа\n"
        "- refresh-токен устанавливается в HttpOnly cookie"
    ),
    responses={
        200: {"description": "Успешный вход."},
        401: {"description": "Неверный логин или пароль."},
        422: {"description": "Ошибка валидации входных данных."},
    },
)
async def login(
    payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    try:
        access_token, refresh_token = await login_user(
            db=db, login=payload.login, password=payload.password
        )
        auth.set_refresh_cookies(refresh_token, response)
    except (InvalidUsernameError, InvalidPasswordError) as error:
        raise HTTPException(status_code=401, detail="Invalid credentials") from error
    else:
        return LoginResponse(access_token=access_token)


@router.post(
    "/refresh",
    response_model=LoginResponse,
    summary="Обновление access-токена",
    description=(
        "Обновляет access-токен по refresh-токену из HttpOnly cookie.\n\n"
        "Результат:\n"
        "- выполняет ротацию refresh-токена (rotation)\n"
        "- возвращает новый access-токен\n"
        "- устанавливает новый refresh-токен в cookie"
    ),
    responses={
        200: {"description": "Токены обновлены."},
        401: {"description": "Refresh-токен недействителен или сессия неактивна."},
        422: {"description": "Ошибка валидации / отсутствует cookie."},
    },
)
async def refresh(
    response: Response,
    payload: TokenPayload = Depends(auth.refresh_token_required),
    refresh_token_raw: RefreshTokenRaw = auth.REFRESH_TOKEN,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    try:
        access_token, new_refresh_token = await refresh_tokens(
            db=db,
            refresh_token_raw=refresh_token_raw,
            payload=payload,
        )
    except (
        InvalidRefreshTokenError,
        RefreshSessionNotFoundError,
        RefreshSessionMismatchError,
    ) as error:
        raise HTTPException(status_code=401, detail=error.reason) from error
    else:
        auth.set_refresh_cookies(new_refresh_token, response)
        return LoginResponse(access_token=access_token)


@router.post(
    "/logout",
    status_code=204,
    summary="Выход из системы",
    description=(
        "Завершает текущую refresh-сессию.\n\n"
        "Поведение:\n"
        "- удаляет refresh-токен из HttpOnly cookie\n"
        "- идемпотентен: повторный вызов также возвращает 204"
    ),
    responses={204: {"description": "Выход выполнен."}},
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> None:
    auth.unset_refresh_cookies(response)

    cookie_name = auth.config.JWT_REFRESH_COOKIE_NAME
    refresh_token_raw = request.cookies.get(cookie_name)

    if not refresh_token_raw:
        return

    await logout_user_idempotent(db=db, refresh_token_raw=refresh_token_raw)
