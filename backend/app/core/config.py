"""Настройки приложения. Любое значение можно переопределить переменной окружения."""
import os
from pathlib import Path

# Одна база на весь проект: necropolis.db в корне (рядом с Necropolis.exe),
# откуда бы ни запускали сервер. config.py -> core -> app -> backend -> корень
_DEFAULT_DB = Path(__file__).resolve().parents[3] / "necropolis.db"


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_DB.as_posix()}")
    # Supabase/Render дают строку вида postgresql://..., SQLAlchemy нужен явный драйвер
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url


class Settings:
    APP_NAME: str = "Цифровой некрополь API"
    DATABASE_URL: str = _database_url()

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me-0f3c9a7e5b1d4e2f8a6c")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
    REFRESH_TOKEN_DAYS: int = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))

    # Защита инфраструктуры
    LOGIN_MAX_ATTEMPTS: int = 5          # неудачных попыток входа...
    LOGIN_WINDOW_SECONDS: int = 300      # ...за 5 минут, потом блокировка
    MAX_BODY_BYTES: int = 1_000_000      # максимальный размер тела запроса
    CORS_ORIGINS: list[str] = [
        o for o in os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1").split(",") if o
    ]

    # Начальные данные
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin123!")


settings = Settings()
