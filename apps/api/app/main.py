from fastapi import FastAPI

from app.auth import router as auth_router
from app.offers import router as offers_router

app = FastAPI(
    title="이음 API",
    version="0.1.0",
    description="이음 1차 모바일웹 업무 API",
)
app.include_router(auth_router)
app.include_router(offers_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ieum-api",
        "phase": "mobile-web-1",
    }
