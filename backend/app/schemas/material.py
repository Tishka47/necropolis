from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserShort

MaterialType = Literal["photo", "document", "text", "link"]


class MaterialCreate(BaseModel):
    type: MaterialType
    title: str = Field(min_length=1, max_length=200)
    file_url: str = Field(default="", max_length=1000,
                          description="Ссылка на файл или сам текст материала")


class MaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    memorial_id: int
    type: MaterialType
    title: str
    file_url: str
    author: UserShort
    created_at: datetime
