from sqlalchemy import select

from app.models import Material
from app.repositories.base import BaseRepository


class MaterialRepository(BaseRepository[Material]):
    model = Material

    def list_for_memorial(self, memorial_id: int) -> list[Material]:
        stmt = (
            select(Material)
            .where(Material.memorial_id == memorial_id)
            .order_by(Material.created_at, Material.id)
        )
        return list(self.db.scalars(stmt).unique())
