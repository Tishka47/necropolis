from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError, UnauthorizedError
from app.core.permissions import Perm
from app.models import Location, Memorial, MemorialStatus, User
from app.repositories.memorial_repository import LocationRepository, MemorialRepository
from app.schemas.memorial import MemorialCreate, MemorialOut, MemorialUpdate
from app.services.base import BaseService


class MemorialService(BaseService):
    def __init__(self, db) -> None:
        super().__init__(db)
        self.memorials = MemorialRepository(db)
        self.locations = LocationRepository(db)

    # ---------- права ----------

    @staticmethod
    def can_view(memorial: Memorial, viewer: User | None) -> bool:
        if memorial.status == MemorialStatus.APPROVED.value:
            return True
        if viewer is None:
            return False
        return memorial.creator_id == viewer.id or viewer.has_permission(Perm.MEMORIAL_VIEW_UNPUBLISHED)

    @staticmethod
    def can_edit(memorial: Memorial, user: User | None) -> bool:
        if user is None:
            return False
        if user.has_permission(Perm.MEMORIAL_EDIT_ANY):
            return True
        return memorial.creator_id == user.id and user.has_permission(Perm.MEMORIAL_EDIT_OWN)

    @staticmethod
    def can_delete(memorial: Memorial, user: User | None) -> bool:
        if user is None:
            return False
        if user.has_permission(Perm.MEMORIAL_DELETE_ANY):
            return True
        return memorial.creator_id == user.id and user.has_permission(Perm.MEMORIAL_DELETE_OWN)

    def to_out(self, memorial: Memorial, viewer: User | None) -> MemorialOut:
        out = MemorialOut.model_validate(memorial)
        return out.model_copy(update={
            "can_edit": self.can_edit(memorial, viewer),
            "can_delete": self.can_delete(memorial, viewer),
            "can_moderate": bool(viewer and viewer.has_permission(Perm.MEMORIAL_MODERATE)),
        })

    # ---------- чтение ----------

    def get_list(
        self, viewer: User | None, *, query: str | None, status: str | None, mine: bool,
        location_id: int | None, offset: int, limit: int,
    ) -> list[Memorial]:
        if mine and viewer is None:
            raise UnauthorizedError("Войдите, чтобы увидеть свои страницы")
        include_unpublished = bool(viewer and viewer.has_permission(Perm.MEMORIAL_VIEW_UNPUBLISHED))
        return self.memorials.search(
            query=query.strip() if query else None,
            status=status,
            creator_id=viewer.id if (mine and viewer) else None,
            location_id=location_id,
            viewer_id=viewer.id if viewer else None,
            include_unpublished=include_unpublished,
            offset=offset,
            limit=limit,
        )

    def get(self, memorial_id: int, viewer: User | None) -> Memorial:
        memorial = self.memorials.get(memorial_id)
        # Неопубликованную чужую страницу отдаём как 404, а не 403:
        # не раскрываем даже сам факт её существования.
        if memorial is None or not self.can_view(memorial, viewer):
            raise NotFoundError("Мемориальная страница не найдена")
        return memorial

    # ---------- изменение ----------

    def _load_locations(self, ids: list[int]) -> list[Location]:
        unique_ids = list(dict.fromkeys(ids))
        found = self.locations.get_many(unique_ids)
        if len(found) != len(unique_ids):
            missing = set(unique_ids) - {loc.id for loc in found}
            raise BadRequestError(f"Места памяти не найдены: {sorted(missing)}")
        return found

    def create(self, data: MemorialCreate, user: User) -> Memorial:
        # Страницы модераторов публикуются сразу, остальные идут на проверку
        status = (
            MemorialStatus.APPROVED.value
            if user.has_permission(Perm.MEMORIAL_MODERATE)
            else MemorialStatus.PENDING.value
        )
        memorial = Memorial(
            creator=user,
            full_name=data.full_name.strip(),
            search_name=Memorial.normalize_name(data.full_name),
            birth_date=data.birth_date,
            death_date=data.death_date,
            biography=data.biography.strip(),
            status=status,
        )
        memorial.locations = self._load_locations(data.location_ids)
        self.memorials.add(memorial)
        self.commit()
        return memorial

    def update(self, memorial_id: int, data: MemorialUpdate, user: User) -> Memorial:
        memorial = self.get(memorial_id, user)
        if not self.can_edit(memorial, user):
            raise ForbiddenError("Нельзя редактировать чужую страницу")

        fields = data.model_dump(exclude_unset=True)  # только реально переданные поля
        location_ids = fields.pop("location_ids", None)
        for not_nullable in ("full_name", "biography"):
            if fields.get(not_nullable, "") is None:
                fields.pop(not_nullable)

        for name, value in fields.items():
            setattr(memorial, name, value.strip() if isinstance(value, str) else value)
        if "full_name" in fields:
            memorial.search_name = Memorial.normalize_name(memorial.full_name)
        if location_ids is not None:
            memorial.locations = self._load_locations(location_ids)

        if memorial.birth_date and memorial.death_date and memorial.death_date < memorial.birth_date:
            self.db.rollback()
            raise BadRequestError("Дата смерти не может быть раньше даты рождения")

        # Правка обычным пользователем снова отправляет страницу на модерацию
        if not user.has_permission(Perm.MEMORIAL_MODERATE):
            memorial.status = MemorialStatus.PENDING.value
        self.commit()
        return memorial

    def replace(self, memorial_id: int, data: MemorialCreate, user: User) -> Memorial:
        """PUT: полная замена всех полей."""
        return self.update(memorial_id, MemorialUpdate(**data.model_dump()), user)

    def delete(self, memorial_id: int, user: User) -> None:
        memorial = self.get(memorial_id, user)
        if not self.can_delete(memorial, user):
            raise ForbiddenError("Нельзя удалить чужую страницу")
        self.memorials.delete(memorial)  # каскадом уйдут материалы и комментарии
        self.commit()

    def set_status(self, memorial_id: int, status: str, moderator: User) -> Memorial:
        memorial = self.get(memorial_id, moderator)
        memorial.status = status
        self.commit()
        return memorial
