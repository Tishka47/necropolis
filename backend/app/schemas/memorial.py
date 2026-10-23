from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.location import LocationOut
from app.schemas.user import UserShort

MemorialStatusLiteral = Literal["pending", "approved", "rejected"]


def _check_dates(birth: date | None, death: date | None) -> None:
    if birth and birth > date.today():
        raise ValueError("Дата рождения не может быть в будущем")
    if death and death > date.today():
        raise ValueError("Дата смерти не может быть в будущем")
    if birth and death and death < birth:
        raise ValueError("Дата смерти не может быть раньше даты рождения")


class MemorialCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200, examples=["Иванов Иван Иванович"])
    birth_date: date | None = Field(default=None, examples=["1931-05-14"])
    death_date: date | None = Field(default=None, examples=["2010-11-02"])
    biography: str = Field(default="", max_length=10000)
    location_ids: list[int] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_dates(self) -> "MemorialCreate":
        _check_dates(self.birth_date, self.death_date)
        return self


class MemorialUpdate(BaseModel):
    """Для PATCH: все поля необязательные, меняются только переданные."""
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    birth_date: date | None = None
    death_date: date | None = None
    biography: str | None = Field(default=None, max_length=10000)
    location_ids: list[int] | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def validate_dates(self) -> "MemorialUpdate":
        _check_dates(self.birth_date, self.death_date)
        return self


class MemorialStatusUpdate(BaseModel):
    status: MemorialStatusLiteral


class MemorialListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    birth_date: date | None
    death_date: date | None
    status: MemorialStatusLiteral
    creator: UserShort
    created_at: datetime


class MemorialOut(MemorialListItem):
    biography: str
    updated_at: datetime
    locations: list[LocationOut]
    # Что текущий пользователь может сделать со страницей. Считается на сервере,
    # клиент только показывает/скрывает кнопки.
    can_edit: bool = False
    can_delete: bool = False
    can_moderate: bool = False
