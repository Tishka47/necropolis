from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import User
from app.schemas.auth import EMAIL_PATTERN


class UserShort(BaseModel):
    """Короткое представление автора: вкладывается в страницы, материалы, комментарии."""
    model_config = ConfigDict(from_attributes=True)  # можно строить прямо из ORM-объекта

    id: int
    username: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    permissions: list[str]
    is_active: bool
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> "UserOut":
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.name,
            permissions=sorted(user.permission_codes),
            is_active=user.is_active,
            created_at=user.created_at,
        )


class UserUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=255, pattern=EMAIL_PATTERN)
    current_password: str | None = Field(default=None, max_length=128)
    new_password: str | None = Field(default=None, min_length=6, max_length=128)


class RoleChangeRequest(BaseModel):
    role: Literal["user", "moderator", "admin"]


class ActiveChangeRequest(BaseModel):
    is_active: bool = Field(description="false — заблокировать, true — разблокировать")
