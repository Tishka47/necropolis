"""Зависимости FastAPI: сессия БД, текущий пользователь, проверка разрешений."""
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.models import User

# OAuth2 Password Flow: Swagger покажет кнопку Authorize и будет брать токен с /api/auth/token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_optional_user(db: DbSession, token: Annotated[str | None, Depends(oauth2_scheme)]) -> User | None:
    """Гость -> None. Невалидный токен -> 401 (клиент обновит его через refresh)."""
    if not token:
        return None
    payload = decode_access_token(token)
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("Пользователь не найден или заблокирован", code="INVALID_TOKEN")
    return user


def get_current_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    if user is None:
        raise UnauthorizedError()
    return user


OptionalUser = Annotated[User | None, Depends(get_optional_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(code: str):
    """Фабрика зависимостей: Depends(require_permission("memorial:moderate"))."""
    def checker(user: CurrentUser) -> User:
        if not user.has_permission(code):
            raise ForbiddenError(f"Недостаточно прав ({code})")
        return user
    return checker
