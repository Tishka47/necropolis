from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError


class BaseService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def commit(self) -> None:
        """Фиксирует транзакцию. При ошибке откатывает её целиком,
        чтобы в БД не осталось половины изменений."""
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Конфликт данных: такая запись уже существует") from exc
        except SQLAlchemyError:
            self.db.rollback()
            raise
