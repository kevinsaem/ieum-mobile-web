import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.offers import router as offers_router

app = FastAPI(
    title="이음 API",
    version="0.1.0",
    description="이음 1차 모바일웹 업무 API",
)
configured_origins = [
    value.strip()
    for value in os.getenv("IEUM_CORS_ORIGINS", "").split(",")
    if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        *configured_origins,
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
