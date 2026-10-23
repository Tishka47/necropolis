from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import CurrentUser, DbSession, OptionalUser, require_permission
from app.core.permissions import Perm
from app.models import User
from app.schemas.common import ErrorResponse
from app.schemas.memorial import (
    MemorialCreate, MemorialListItem, MemorialOut, MemorialStatusLiteral, MemorialStatusUpdate,
    MemorialUpdate,
)
from app.services.memorial_service import MemorialService

router = APIRouter(prefix="/api/memorials", tags=["Мемориальные страницы"])

ERRORS = {
    400: {"model": ErrorResponse}, 401: {"model": ErrorResponse},
    403: {"model": ErrorResponse}, 404: {"model": ErrorResponse},
}
Creator = Annotated[User, Depends(require_permission(Perm.MEMORIAL_CREATE))]
Moderator = Annotated[User, Depends(require_permission(Perm.MEMORIAL_MODERATE))]


def _list(db, viewer, q, status, mine, location_id, offset, limit) -> list[MemorialListItem]:
    items = MemorialService(db).get_list(
        viewer, query=q, status=status, mine=mine,
        location_id=location_id, offset=offset, limit=limit,
    )
    return [MemorialListItem.model_validate(m) for m in items]


@router.get("", response_model=list[MemorialListItem], responses=ERRORS,
            summary="Список страниц с фильтрами")
def list_memorials(
    db: DbSession,
    viewer: OptionalUser,
    q: str | None = Query(None, max_length=100, description="Часть ФИО"),
    status: MemorialStatusLiteral | None = Query(None),
    mine: bool = Query(False, description="Только мои страницы"),
    location_id: int | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return _list(db, viewer, q, status, mine, location_id, offset, limit)


# /search объявлен ДО /{memorial_id}, иначе FastAPI попытается разобрать "search" как id
@router.get("/search", response_model=list[MemorialListItem], responses=ERRORS,
            summary="Поиск по ФИО")
def search_memorials(
    db: DbSession,
    viewer: OptionalUser,
    q: str = Query(min_length=1, max_length=100),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return _list(db, viewer, q, None, False, None, offset, limit)


@router.get("/{memorial_id}", response_model=MemorialOut, responses=ERRORS, summary="Одна страница")
def get_memorial(memorial_id: int, db: DbSession, viewer: OptionalUser):
    service = MemorialService(db)
    return service.to_out(service.get(memorial_id, viewer), viewer)


@router.post("", response_model=MemorialOut, status_code=201, responses=ERRORS, summary="Создать страницу")
def create_memorial(data: MemorialCreate, user: Creator, db: DbSession):
    service = MemorialService(db)
    return service.to_out(service.create(data, user), user)


@router.patch("/{memorial_id}", response_model=MemorialOut, responses=ERRORS,
              summary="Частично изменить страницу")
def update_memorial(memorial_id: int, data: MemorialUpdate, user: CurrentUser, db: DbSession):
    service = MemorialService(db)
    return service.to_out(service.update(memorial_id, data, user), user)


@router.put("/{memorial_id}", response_model=MemorialOut, responses=ERRORS,
            summary="Полностью заменить страницу")
def replace_memorial(memorial_id: int, data: MemorialCreate, user: CurrentUser, db: DbSession):
    service = MemorialService(db)
    return service.to_out(service.replace(memorial_id, data, user), user)


@router.delete("/{memorial_id}", status_code=204, response_class=Response, responses=ERRORS,
               summary="Удалить страницу")
def delete_memorial(memorial_id: int, user: CurrentUser, db: DbSession):
    MemorialService(db).delete(memorial_id, user)
    return Response(status_code=204)


@router.patch("/{memorial_id}/status", response_model=MemorialOut, responses=ERRORS,
              summary="Модерация: опубликовать / отклонить")
def set_status(memorial_id: int, data: MemorialStatusUpdate, moderator: Moderator, db: DbSession):
    service = MemorialService(db)
    return service.to_out(service.set_status(memorial_id, data.status, moderator), moderator)
