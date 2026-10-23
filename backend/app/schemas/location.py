from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    address: str = Field(default="", max_length=255)
    description: str = Field(default="", max_length=5000)


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    description: str
