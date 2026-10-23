"""Пользователи и их refresh-токены."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.role import Role

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.material import Material
    from app.models.memorial import Memorial


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    is_active: Mapped[bool] = mapped_column(default=True)

    # многие-к-одному: lazy="joined" -> роль приходит тем же запросом через JOIN
    role: Mapped[Role] = relationship(back_populates="users", lazy="joined")
    memorials: Mapped[list["Memorial"]] = relationship(back_populates="creator")
    materials: Mapped[list["Material"]] = relationship(back_populates="author")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def permission_codes(self) -> set[str]:
        return {p.code for p in self.role.permissions} if self.role else set()

    def has_permission(self, code: str) -> bool:
        return code in self.permission_codes


class RefreshToken(TimestampMixin, Base):
    """Каждая выданная сессия. Храним хэш, а не сам токен: утечка БД не даёт войти."""
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(default=False)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")
