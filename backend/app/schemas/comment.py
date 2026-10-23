from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserShort


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    memorial_id: int
    text: str
    author: UserShort
    created_at: datetime
