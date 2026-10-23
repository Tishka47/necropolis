"""Мемориальные страницы и места памяти."""
import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, utcnow

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.material import Material
    from app.models.user import User


class MemorialStatus(str, enum.Enum):
    PENDING = "pending"      # на модерации
    APPROVED = "approved"    # опубликована
    REJECTED = "rejected"    # отклонена


# Таблица 7 из проектной документации: связь страница <-> место (многие-ко-многим)
memorial_locations = Table(
    "memorial_locations",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("memorial_id", ForeignKey("memorials.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("location_id", ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True),
    UniqueConstraint("memorial_id", "location_id", name="uq_memorial_location"),
)


class Location(Base):
    """Место памяти: кладбище, мемориал, памятник."""
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    address: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")

    memorials: Mapped[list["Memorial"]] = relationship(
        secondary=memorial_locations, back_populates="locations"
    )


class Memorial(TimestampMixin, Base):
    """Центральная сущность системы."""
    __tablename__ = "memorials"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    # Нормализованное ФИО для поиска: SQLite lower() не понимает кириллицу,
    # поэтому приводим к нижнему регистру в Python и храним отдельно.
    search_name: Mapped[str] = mapped_column(String(200), index=True)
    birth_date: Mapped[date | None] = mapped_column(Date, default=None)
    death_date: Mapped[date | None] = mapped_column(Date, default=None)
    biography: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default=MemorialStatus.PENDING.value, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    creator: Mapped["User"] = relationship(back_populates="memorials", lazy="joined")
    # cascade="all, delete-orphan": удалили страницу -> ORM удалит её материалы и комментарии
    materials: Mapped[list["Material"]] = relationship(
        back_populates="memorial", cascade="all, delete-orphan", order_by="Material.created_at"
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="memorial", cascade="all, delete-orphan", order_by="Comment.created_at"
    )
    locations: Mapped[list[Location]] = relationship(
        secondary=memorial_locations, back_populates="memorials",
        lazy="selectin", order_by=Location.name,
    )

    @staticmethod
    def normalize_name(value: str) -> str:
        return " ".join(value.replace("ё", "е").replace("Ё", "Е").split()).casefold()
