"""Памятные материалы: фото, документы, тексты, ссылки."""
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.memorial import Memorial
    from app.models.user import User


class Material(TimestampMixin, Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    memorial_id: Mapped[int] = mapped_column(ForeignKey("memorials.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    file_url: Mapped[str] = mapped_column(String(1000), default="")

    memorial: Mapped["Memorial"] = relationship(back_populates="materials")
    author: Mapped["User"] = relationship(back_populates="materials", lazy="joined")
