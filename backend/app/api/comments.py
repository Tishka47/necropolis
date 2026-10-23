from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import CurrentUser, DbSession, OptionalUser, require_permission
from app.core.permissions import Perm
from app.models import User
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.common import ErrorResponse
from app.services.comment_service import CommentService

router = APIRouter(prefix="/api", tags=["Воспоминания"])
ERRORS = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}}
Commenter = Annotated[User, Depends(require_permission(Perm.COMMENT_CREATE))]


@router.get("/memorials/{memorial_id}/comments", response_model=list[CommentOut], responses=ERRORS,
            summary="Воспоминания на странице")
def list_comments(memorial_id: int, db: DbSession, viewer: OptionalUser):
    return [CommentOut.model_validate(c) for c in CommentService(db).get_list(memorial_id, viewer)]


@router.post("/memorials/{memorial_id}/comments", response_model=CommentOut, status_code=201,
             responses=ERRORS, summary="Оставить воспоминание")
def add_comment(memorial_id: int, data: CommentCreate, user: Commenter, db: DbSession):
    return CommentOut.model_validate(CommentService(db).add(memorial_id, data.text, user))


@router.delete("/comments/{comment_id}", status_code=204, response_class=Response, responses=ERRORS,
               summary="Удалить воспоминание")
def delete_comment(comment_id: int, user: CurrentUser, db: DbSession):
    CommentService(db).delete(comment_id, user)
    return Response(status_code=204)
