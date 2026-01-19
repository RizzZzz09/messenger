import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get(
    "/health", summary="Проверка", tags=["Технические"], description="Проверка работоспособности"
)
async def root() -> dict[str, str]:
    return {"message": "Hello World!"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)
