from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DbSession
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.schemas.common import ErrorResponse
from app.schemas.user import UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Авторизация"])

ERRORS = {400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}}


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserOut, status_code=201, responses=ERRORS,
             summary="Регистрация")
def register(data: RegisterRequest, db: DbSession):
    return UserOut.from_user(AuthService(db).register(data))


@router.post("/login", response_model=TokenPair, responses={**ERRORS, 429: {"model": ErrorResponse}},
             summary="Вход (логин/email + пароль)")
def login(data: LoginRequest, request: Request, db: DbSession):
    return AuthService(db).login(data.login, data.password, _client_ip(request))


@router.post("/token", response_model=TokenPair, responses=ERRORS,
             summary="OAuth2 Password Flow (форма для кнопки Authorize в Swagger)")
def oauth2_token(form: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request, db: DbSession):
    return AuthService(db).login(form.username, form.password, _client_ip(request))


@router.post("/refresh", response_model=TokenPair, responses=ERRORS,
             summary="Обновить пару токенов по refresh-токену")
def refresh(data: RefreshRequest, db: DbSession):
    return AuthService(db).refresh(data.refresh_token)


@router.post("/logout", status_code=204, response_class=Response, summary="Выход (отзыв refresh-токена)")
def logout(data: RefreshRequest, db: DbSession):
    AuthService(db).logout(data.refresh_token)
    return Response(status_code=204)
