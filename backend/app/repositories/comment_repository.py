from sqlalchemy import select

from app.models import Comment
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    model = Comment

    def list_for_memorial(self, memorial_id: int) -> list[Comment]:
        stmt = (
            select(Comment)
            .where(Comment.memorial_id == memorial_id)
            .order_by(Comment.created_at, Comment.id)
        )
        return list(self.db.scalars(stmt).unique())
