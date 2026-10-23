"""Воспоминания (комментарии) к мемориальной странице."""
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.memorial import Memorial
    from app.models.user import User


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    memorial_id: Mapped[int] = mapped_column(ForeignKey("memorials.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    text: Mapped[str] = mapped_column(Text)

    memorial: Mapped["Memorial"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments", lazy="joined")
