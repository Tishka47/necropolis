from sqlalchemy import or_, select

from app.models import Location, Memorial, MemorialStatus
from app.repositories.base import BaseRepository


class MemorialRepository(BaseRepository[Memorial]):
    model = Memorial

    def search(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        creator_id: int | None = None,
        location_id: int | None = None,
        viewer_id: int | None = None,
        include_unpublished: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Memorial]:
        stmt = select(Memorial)

        if not include_unpublished:
            # Обычный пользователь видит опубликованные + свои (даже на модерации)
            visible = Memorial.status == MemorialStatus.APPROVED.value
            if viewer_id is not None:
                visible = or_(visible, Memorial.creator_id == viewer_id)
            stmt = stmt.where(visible)

        if status:
            stmt = stmt.where(Memorial.status == status)
        if creator_id is not None:
            stmt = stmt.where(Memorial.creator_id == creator_id)
        if query:
            # autoescape: символы % и _ из запроса не считаются шаблоном LIKE
            stmt = stmt.where(
                Memorial.search_name.contains(Memorial.normalize_name(query), autoescape=True)
            )
        if location_id is not None:
            # any() -> EXISTS-подзапрос по связи многие-ко-многим
            stmt = stmt.where(Memorial.locations.any(Location.id == location_id))

        stmt = stmt.order_by(Memorial.created_at.desc(), Memorial.id.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).unique())


class LocationRepository(BaseRepository[Location]):
    model = Location

    def get_all_sorted(self) -> list[Location]:
        return list(self.db.scalars(select(Location).order_by(Location.name)))

    def get_many(self, ids: list[int]) -> list[Location]:
        if not ids:
            return []
        return list(self.db.scalars(select(Location).where(Location.id.in_(ids))))
