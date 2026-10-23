from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.permissions import Perm
from app.models import Material, User
from app.repositories.material_repository import MaterialRepository
from app.schemas.material import MaterialCreate
from app.services.base import BaseService
from app.services.memorial_service import MemorialService


class MaterialService(BaseService):
    def __init__(self, db) -> None:
        super().__init__(db)
        self.materials = MaterialRepository(db)
        self.memorial_service = MemorialService(db)

    def get_list(self, memorial_id: int, viewer: User | None) -> list[Material]:
        self.memorial_service.get(memorial_id, viewer)  # 404, если страницу видеть нельзя
        return self.materials.list_for_memorial(memorial_id)

    def add(self, memorial_id: int, data: MaterialCreate, user: User) -> Material:
        memorial = self.memorial_service.get(memorial_id, user)
        if not self.memorial_service.can_edit(memorial, user):
            raise ForbiddenError("Добавлять материалы может только автор страницы или модератор")
        material = Material(
            memorial=memorial, author=user, type=data.type,
            title=data.title.strip(), file_url=data.file_url.strip(),
        )
        self.materials.add(material)
        self.commit()
        return material

    def delete(self, material_id: int, user: User) -> None:
        material = self.materials.get(material_id)
        if material is None:
            raise NotFoundError("Материал не найден")
        allowed = (
            material.author_id == user.id
            or material.memorial.creator_id == user.id
            or user.has_permission(Perm.MATERIAL_DELETE_ANY)
        )
        if not allowed:
            raise ForbiddenError("Нельзя удалить чужой материал")
        self.materials.delete(material)
        self.commit()
