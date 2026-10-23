"""Репозиторий = единственное место, где пишутся запросы к БД.
Сервисы не строят select() сами, а просят репозиторий."""
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, obj_id: int) -> ModelT | None:
        # Session.get ищет по первичному ключу, сначала в identity map сессии
        return self.db.get(self.model, obj_id)

    def get_all(self, offset: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.db.scalars(stmt))

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()  # отправляет INSERT без commit, чтобы получить id
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()
