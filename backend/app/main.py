"""Точка входа: сборка приложения из слоёв."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api import auth, comments, locations, materials, memorials, users
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.error_handlers import register_error_handlers
from app.core.middleware import register_security_middleware
from app.models import Base
from app.seed import seed

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)  # создаёт таблицы по описанию моделей
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="API мобильного приложения «Цифровой некрополь». "
                "Авторизация: кнопка Authorize (логин admin / Admin123!).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
register_security_middleware(app)
register_error_handlers(app)

for module in (auth, users, memorials, materials, comments, locations):
    app.include_router(module.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/api/health", tags=["Служебное"], summary="Проверка, что сервер жив")
def health():
    return {"status": "ok"}
