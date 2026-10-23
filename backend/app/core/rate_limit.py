"""Ограничение перебора паролей: N неудачных попыток за окно времени -> 429."""
import time
from collections import defaultdict, deque
from threading import Lock

from app.core.config import settings
from app.core.exceptions import TooManyRequestsError


class LoginRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        attempts = self._failures[key]
        while attempts and now - attempts[0] > self.window:
            attempts.popleft()
        return attempts

    def check(self, key: str) -> None:
        with self._lock:
            now = time.monotonic()
            attempts = self._prune(key, now)
            if len(attempts) >= self.max_attempts:
                retry_after = int(self.window - (now - attempts[0])) + 1
                raise TooManyRequestsError(
                    f"Слишком много неудачных попыток входа. Повторите через {retry_after} с."
                )

    def register_failure(self, key: str) -> None:
        with self._lock:
            self._failures[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


login_limiter = LoginRateLimiter(settings.LOGIN_MAX_ATTEMPTS, settings.LOGIN_WINDOW_SECONDS)
