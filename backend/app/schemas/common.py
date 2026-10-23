from pydantic import BaseModel


class MessageResponse(BaseModel):
    detail: str


class ErrorResponse(BaseModel):
    """Формат любой ошибки API (для документации Swagger)."""
    detail: str
    code: str
