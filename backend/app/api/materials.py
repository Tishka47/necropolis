from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import CurrentUser, DbSession, OptionalUser, require_permission
from app.core.permissions import Perm
from app.models import User
from app.schemas.common import ErrorResponse
from app.schemas.material import MaterialCreate, MaterialOut
from app.services.material_service import MaterialService

router = APIRouter(prefix="/api", tags=["Материалы"])
ERRORS = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
MaterialAuthor = Annotated[User, Depends(require_permission(Perm.MATERIAL_ADD))]


@router.get("/memorials/{memorial_id}/materials", response_model=list[MaterialOut], responses=ERRORS,
            summary="Материалы страницы")
def list_materials(memorial_id: int, db: DbSession, viewer: OptionalUser):
    return [MaterialOut.model_validate(m) for m in MaterialService(db).get_list(memorial_id, viewer)]


@router.post("/memorials/{memorial_id}/materials", response_model=MaterialOut, status_code=201,
             responses=ERRORS, summary="Добавить материал")
def add_material(memorial_id: int, data: MaterialCreate, user: MaterialAuthor, db: DbSession):
    return MaterialOut.model_validate(MaterialService(db).add(memorial_id, data, user))


@router.delete("/materials/{material_id}", status_code=204, response_class=Response, responses=ERRORS,
               summary="Удалить материал")
def delete_material(material_id: int, user: CurrentUser, db: DbSession):
    MaterialService(db).delete(material_id, user)
    return Response(status_code=204)
