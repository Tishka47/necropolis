from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.permissions import Perm
from app.core.security import hash_password, verify_password
from app.models import User
from app.repositories.user_repository import RefreshTokenRepository, RoleRepository, UserRepository
from app.schemas.user import UserUpdate
from app.services.base import BaseService


class UserService(BaseService):
    def __init__(self, db) -> None:
        super().__init__(db)
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.tokens = RefreshTokenRepository(db)

    def get(self, user_id: int, viewer: User) -> User:
        if viewer.id != user_id and not viewer.has_permission(Perm.USER_MANAGE):
            raise ForbiddenError("Можно просматривать только свой профиль")
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Пользователь не найден")
        return user

    def list_all(self, offset: int, limit: int) -> list[User]:
        return self.users.get_all(offset, limit)

    def update_me(self, user: User, data: UserUpdate) -> User:
        if data.email is not None:
            email = data.email.lower()
            other = self.users.get_by_email(email)
            if other is not None and other.id != user.id:
                raise ConflictError("Этот email уже используется")
            user.email = email
        if data.new_password is not None:
            if not data.current_password or not verify_password(data.current_password, user.password_hash):
                raise BadRequestError("Текущий пароль указан неверно")
            user.password_hash = hash_password(data.new_password)
        self.commit()
        return user

    def change_role(self, user_id: int, role_name: str, admin: User) -> User:
        if user_id == admin.id:
            raise BadRequestError("Нельзя изменить собственную роль")
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Пользователь не найден")
        role = self.roles.get_by_name(role_name)
        if role is None:
            raise NotFoundError("Роль не найдена")
        user.role = role
        self.commit()
        return user

    def set_active(self, user_id: int, is_active: bool, admin: User) -> User:
        """Блокировка: заблокированный не может войти, а его сессии сразу завершаются."""
        if user_id == admin.id:
            raise BadRequestError("Нельзя заблокировать самого себя")
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Пользователь не найден")
        user.is_active = is_active
        if not is_active:
            self.tokens.revoke_all_for_user(user.id)
        self.commit()
        return user
