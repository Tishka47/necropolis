"""Базовый класс всех ORM-моделей (SQLAlchemy 2.0, декларативный стиль)."""
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Текущее время в UTC без tzinfo (SQLite не хранит часовые пояса)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    """От этого класса наследуются все модели. В Base.metadata собирается описание
    всех таблиц, по нему create_all() создаёт схему БД."""


class TimestampMixin:
    """Миксин: добавляет колонку created_at в любую модель."""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
