"""Запросы к API выполняются в фоновом потоке, чтобы интерфейс не зависал.
Результат возвращается в главный поток Kivy через Clock (менять виджеты можно только из него)."""
import threading

from kivy.app import App
from kivy.clock import Clock

from services.api_client import ApiError


def _default_error(err: ApiError) -> None:
    App.get_running_app().show_error(err)


def run_async(func, on_success=None, on_error=None) -> None:
    def worker():
        try:
            result = func()
        except ApiError as exc:
            error = exc
        except Exception as exc:  # непредвиденная ошибка клиента
            error = ApiError(0, f"Непредвиденная ошибка: {exc}")
        else:
            if on_success is not None:
                Clock.schedule_once(lambda _dt: on_success(result))
            return
        handler = on_error or _default_error
        Clock.schedule_once(lambda _dt: handler(error))

    threading.Thread(target=worker, daemon=True).start()
