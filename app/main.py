import uvicorn
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.routes.auth import router as auth_router

app = FastAPI(
    title="Messenger API",
    description=(
        "Backend API для мессенджера.\n\n"
        "Включает регистрацию, авторизацию (JWT), управление пользователями и сообщениями."
    ),
    version="0.1.0",
)


@app.get("/health/db")
async def health(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}


app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)
