"""Импорт всех моделей в одном месте, чтобы SQLAlchemy знал обо всех таблицах
и мог связать relationship("User") и т.п. по именам."""
from app.models.base import Base
from app.models.role import Permission, Role, role_permissions
from app.models.user import RefreshToken, User
from app.models.memorial import Location, Memorial, MemorialStatus, memorial_locations
from app.models.material import Material
from app.models.comment import Comment

__all__ = [
    "Base", "Permission", "Role", "role_permissions", "User", "RefreshToken",
    "Location", "Memorial", "MemorialStatus", "memorial_locations", "Material", "Comment",
]
