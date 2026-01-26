from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.services.auth import register_user
from app.services.errors import (
    EmailAlreadyExistsError,
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
