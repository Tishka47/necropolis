from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_permission
from app.core.permissions import Perm
from app.models import User
from app.schemas.common import ErrorResponse
from app.schemas.user import ActiveChangeRequest, RoleChangeRequest, UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Пользователи"])

ERRORS = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
Admin = Annotated[User, Depends(require_permission(Perm.USER_MANAGE))]


@router.get("/me", response_model=UserOut, responses=ERRORS, summary="Мой профиль")
def get_me(user: CurrentUser):
    return UserOut.from_user(user)


@router.patch("/me", response_model=UserOut, responses=ERRORS, summary="Изменить email/пароль")
def update_me(data: UserUpdate, user: CurrentUser, db: DbSession):
    return UserOut.from_user(UserService(db).update_me(user, data))


@router.get("", response_model=list[UserOut], responses=ERRORS, summary="Все пользователи (админ)")
def list_users(_admin: Admin, db: DbSession,
               offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    return [UserOut.from_user(u) for u in UserService(db).list_all(offset, limit)]


@router.get("/{user_id}", response_model=UserOut, responses=ERRORS, summary="Профиль пользователя")
def get_user(user_id: int, viewer: CurrentUser, db: DbSession):
    return UserOut.from_user(UserService(db).get(user_id, viewer))


@router.patch("/{user_id}/role", response_model=UserOut, responses=ERRORS, summary="Сменить роль (админ)")
def change_role(user_id: int, data: RoleChangeRequest, admin: Admin, db: DbSession):
    return UserOut.from_user(UserService(db).change_role(user_id, data.role, admin))


@router.patch("/{user_id}/active", response_model=UserOut, responses=ERRORS,
              summary="Заблокировать / разблокировать (админ)")
def set_active(user_id: int, data: ActiveChangeRequest, admin: Admin, db: DbSession):
    return UserOut.from_user(UserService(db).set_active(user_id, data.is_active, admin))
