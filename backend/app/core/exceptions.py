"""Прикладные исключения. Сервисы бросают их, а обработчики в error_handlers.py
превращают в JSON-ответ с нужным HTTP-кодом. Так бизнес-логика не знает о HTTP."""


class AppError(Exception):
    status_code: int = 400
    code: str = "BAD_REQUEST"
    default_detail: str = "Некорректный запрос"

    def __init__(self, detail: str | None = None, code: str | None = None) -> None:
        self.detail = detail or self.default_detail
        if code:
            self.code = code
        super().__init__(self.detail)


class BadRequestError(AppError):
    status_code = 400
    code = "BAD_REQUEST"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"
    default_detail = "Требуется авторизация"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"
    default_detail = "Недостаточно прав для этого действия"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    default_detail = "Объект не найден"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
    default_detail = "Конфликт данных"


class TooManyRequestsError(AppError):
    status_code = 429
    code = "TOO_MANY_REQUESTS"
    default_detail = "Слишком много запросов"
