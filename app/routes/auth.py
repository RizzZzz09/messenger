from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import auth
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth import login_user, register_user
from app.services.errors import (
    EmailAlreadyExistsError,
    InvalidPasswordError,
    InvalidUsernameError,
    UsernameAlreadyExistsError,
    UsernameContainsWhitespaceError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
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


@router.post("/login", response_model=LoginResponse)
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
