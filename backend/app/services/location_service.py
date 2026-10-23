from app.models import Location
from app.repositories.memorial_repository import LocationRepository
from app.schemas.location import LocationCreate
from app.services.base import BaseService


class LocationService(BaseService):
    def __init__(self, db) -> None:
        super().__init__(db)
        self.locations = LocationRepository(db)

    def get_list(self) -> list[Location]:
        return self.locations.get_all_sorted()

    def create(self, data: LocationCreate) -> Location:
        location = Location(
            name=data.name.strip(), address=data.address.strip(),
            description=data.description.strip(),
        )
        self.locations.add(location)
        self.commit()
        return location
