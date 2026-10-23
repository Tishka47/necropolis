"""Пароли, JWT access-токены и refresh-токены.
Без внешних крипто-библиотек: PBKDF2 из стандартной библиотеки + PyJWT."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    """Соль + 200 000 итераций PBKDF2-SHA256. В БД пароль в открытом виде не хранится."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
    )
    # compare_digest сравнивает за постоянное время: защита от timing-атак
    return hmac.compare_digest(digest.hex(), digest_hex)


# Хэш-пустышка: проверяем по нему, если пользователя нет, чтобы время ответа
# не выдавало, существует ли логин.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_hex(8))


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Срок действия токена истёк", code="TOKEN_EXPIRED") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Недействительный токен", code="INVALID_TOKEN") from exc
    if payload.get("type") != "access" or "sub" not in payload:
        raise UnauthorizedError("Недействительный токен", code="INVALID_TOKEN")
    return payload


def generate_refresh_token() -> str:
    """Случайная строка. Клиенту отдаём её, в БД храним только SHA-256 хэш."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
