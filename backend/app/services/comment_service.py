from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.permissions import Perm
from app.models import Comment, MemorialStatus, User
from app.repositories.comment_repository import CommentRepository
from app.services.base import BaseService
from app.services.memorial_service import MemorialService


class CommentService(BaseService):
    def __init__(self, db) -> None:
        super().__init__(db)
        self.comments = CommentRepository(db)
        self.memorial_service = MemorialService(db)

    def get_list(self, memorial_id: int, viewer: User | None) -> list[Comment]:
        self.memorial_service.get(memorial_id, viewer)
        return self.comments.list_for_memorial(memorial_id)

    def add(self, memorial_id: int, text: str, user: User) -> Comment:
        memorial = self.memorial_service.get(memorial_id, user)
        if memorial.status != MemorialStatus.APPROVED.value:
            raise BadRequestError("Оставлять воспоминания можно только на опубликованных страницах")
        text = text.strip()
        if not text:
            raise BadRequestError("Текст воспоминания не может быть пустым")
        comment = Comment(memorial=memorial, author=user, text=text)
        self.comments.add(comment)
        self.commit()
        return comment

    def delete(self, comment_id: int, user: User) -> None:
        comment = self.comments.get(comment_id)
        if comment is None:
            raise NotFoundError("Воспоминание не найдено")
        if comment.user_id != user.id and not user.has_permission(Perm.COMMENT_DELETE_ANY):
            raise ForbiddenError("Нельзя удалить чужое воспоминание")
        self.comments.delete(comment)
        self.commit()
