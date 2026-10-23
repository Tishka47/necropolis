"""Защитные HTTP-заголовки и ограничение размера тела запроса."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings


def register_security_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def security_middleware(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > settings.MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "Слишком большой запрос", "code": "PAYLOAD_TOO_LARGE"},
            )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response
