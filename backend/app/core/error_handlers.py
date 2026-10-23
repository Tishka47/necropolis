"""Единый формат ошибок: {"detail": "...", "code": "..."}.
400 - ошибки валидации, 401 - нет/плохой токен, 404 - не найдено, 500 - всё непредвиденное."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError

logger = logging.getLogger("necropolis")


def _error(status: int, detail: str, code: str, headers: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": detail, "code": code}, headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return _error(exc.status_code, exc.detail, exc.code, headers)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        messages = []
        for err in exc.errors():
            location = ".".join(
                str(part) for part in err.get("loc", []) if part not in ("body", "query", "path")
            )
            message = str(err.get("msg", "")).removeprefix("Value error, ")
            messages.append(f"{location}: {message}" if location else message)
        return _error(400, "; ".join(messages) or "Некорректные данные", "VALIDATION_ERROR")

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Ошибка запроса"
        if exc.status_code == 404 and detail == "Not Found":
            detail = "Адрес не найден"
        return _error(exc.status_code, detail, "HTTP_ERROR")

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Стектрейс пишем в лог сервера, а клиенту не показываем внутренности
        logger.exception("Необработанная ошибка на %s %s", request.method, request.url.path)
        return _error(500, "Внутренняя ошибка сервера", "INTERNAL_ERROR")
