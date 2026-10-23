from datetime import timedelta

from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from app.core.permissions import DEFAULT_ROLE
from app.core.rate_limit import login_limiter
from app.core.security import (
    DUMMY_PASSWORD_HASH, create_access_token, generate_refresh_token, hash_password,
    hash_token, verify_password,
)
from app.models import RefreshToken, User
from app.models.base import utcnow
from app.repositories.user_repository import (
    RefreshTokenRepository, RoleRepository, UserRepository,
)
from app.schemas.auth import RegisterRequest, TokenPair
from app.services.base import BaseService


class AuthService(BaseService):
    def __init__(self, db) -> None:
        super().__init__(db)
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.tokens = RefreshTokenRepository(db)

    # ---------- регистрация и вход ----------

    def register(self, data: RegisterRequest) -> User:
        if self.users.get_by_username(data.username):
            raise ConflictError("Пользователь с таким логином уже существует")
        if self.users.get_by_email(data.email):
            raise ConflictError("Этот email уже зарегистрирован")
        role = self.roles.get_by_name(DEFAULT_ROLE)
        if role is None:
            raise RuntimeError("Роли не созданы: не выполнено заполнение БД")

        user = User(
            username=data.username,
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            role=role,
        )
        self.users.add(user)
        self.commit()
        return user

    def login(self, login: str, password: str, client_ip: str) -> TokenPair:
        limiter_key = f"{client_ip}:{login.strip().lower()}"
        login_limiter.check(limiter_key)

        user = self.users.get_by_login(login)
        password_ok = verify_password(password, user.password_hash if user else DUMMY_PASSWORD_HASH)
        if user is None or not password_ok:
            login_limiter.register_failure(limiter_key)
            raise UnauthorizedError("Неверный логин или пароль", code="INVALID_CREDENTIALS")
        if not user.is_active:
            raise ForbiddenError("Учётная запись заблокирована")

        login_limiter.reset(limiter_key)
        return self._issue_tokens(user)

    # ---------- токены ----------

    def _issue_tokens(self, user: User) -> TokenPair:
        raw_refresh = generate_refresh_token()
        self.tokens.add(RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            expires_at=utcnow() + timedelta(days=settings.REFRESH_TOKEN_DAYS),
        ))
        self.commit()
        return TokenPair(
            access_token=create_access_token(user.id, user.role.name),
            refresh_token=raw_refresh,
            expires_in=settings.ACCESS_TOKEN_MINUTES * 60,
        )

    def refresh(self, raw_refresh: str) -> TokenPair:
        """Ротация: старый refresh-токен гасится, выдаётся новая пара.
        Если кто-то предъявил уже погашенный токен, значит его украли:
        завершаем ВСЕ сессии пользователя."""
        token = self.tokens.get_by_hash(hash_token(raw_refresh))
        if token is None:
            raise UnauthorizedError("Недействительный refresh-токен", code="INVALID_REFRESH")
        if token.revoked:
            self.tokens.revoke_all_for_user(token.user_id)
            self.commit()
            raise UnauthorizedError(
                "Токен уже был использован. В целях безопасности все сессии завершены.",
                code="REFRESH_REUSED",
            )
        if token.expires_at < utcnow():
            raise UnauthorizedError("Сессия истекла, войдите заново", code="REFRESH_EXPIRED")
        if not token.user.is_active:
            raise ForbiddenError("Учётная запись заблокирована")

        token.revoked = True
        return self._issue_tokens(token.user)  # внутри один commit на оба изменения

    def logout(self, raw_refresh: str) -> None:
        token = self.tokens.get_by_hash(hash_token(raw_refresh))
        if token and not token.revoked:
            token.revoked = True
            self.commit()
