from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_permission
from app.core.permissions import Perm
from app.models import User
from app.schemas.common import ErrorResponse
from app.schemas.location import LocationCreate, LocationOut
from app.services.location_service import LocationService

router = APIRouter(prefix="/api/locations", tags=["Места памяти"])
Manager = Annotated[User, Depends(require_permission(Perm.LOCATION_MANAGE))]


@router.get("", response_model=list[LocationOut], summary="Все места памяти")
def list_locations(db: DbSession):
    return [LocationOut.model_validate(loc) for loc in LocationService(db).get_list()]


@router.post("", response_model=LocationOut, status_code=201,
             responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
             summary="Добавить место (модератор)")
def create_location(data: LocationCreate, _user: Manager, db: DbSession):
    return LocationOut.model_validate(LocationService(db).create(data))
