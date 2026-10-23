"""Мобильное приложение «Цифровой некрополь» (Kivy).
Запуск: python main.py. На компьютере сервер API поднимается сам (services/local_server.py),
если он не запущен отдельно и в окружении есть зависимости backend."""
import os
import sys

if getattr(sys, "frozen", False) and sys.stderr is None:
    # .exe без консоли: пишем логи Kivy и сервера в файл рядом с программой, а не в никуда
    _log = open(os.path.join(os.path.dirname(sys.executable), "necropolis.log"), "w", encoding="utf-8")
    sys.stdout = sys.stderr = _log

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.utils import platform

import theme
from config import API_URL, CLOUD_URL
from screens import (
    AdminScreen, DetailScreen, FormScreen, ListScreen, LoginScreen, MainScreen, ProfileScreen,
    RegisterScreen,
)
from services import local_server
from services.api_client import ApiClient, ApiError
from services.async_task import run_async
from widgets.dialogs import confirm, notify, prompt

KV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kv")
AUTH_SCREENS = ("login", "register")


class NecropolisApp(App):
    title = "Цифровой некрополь"

    user = ObjectProperty(None, allownone=True)   # dict из /api/users/me или None
    username = StringProperty("Гость")
    role = StringProperty("guest")
    is_guest = BooleanProperty(True)
    permissions = ListProperty([])
    server_info = StringProperty("")              # строка про сервер на экране входа

    # ---------- запуск ----------

    def build(self):
        if platform not in ("android", "ios"):
            Window.size = (400, 780)
        Window.softinput_mode = "below_target"   # клавиатура не перекрывает поле ввода
        Window.bind(on_keyboard=self._on_keyboard)

        self.store = JsonStore(os.path.join(self.user_data_dir, "session.json"))
        theme.P.apply(self._saved_theme())
        Window.clearcolor = theme.P.BG
        theme.P.bind(BG=lambda _palette, color: setattr(Window, "clearcolor", color))

        theme.register_fonts()
        for name in sorted(os.listdir(KV_DIR)):    # 00_theme.kv грузится первым
            if name.endswith(".kv"):
                Builder.load_file(os.path.join(KV_DIR, name))

        self.api = ApiClient(self._saved_api_url(), on_refresh_token_changed=self._save_refresh_token)

        self.sm = ScreenManager(transition=SlideTransition(duration=0.18))
        for screen_cls, name in (
            (LoginScreen, "login"), (RegisterScreen, "register"), (MainScreen, "main"),
            (ListScreen, "list"), (DetailScreen, "detail"), (FormScreen, "form"),
            (ProfileScreen, "profile"), (AdminScreen, "admin"),
        ):
            self.sm.add_widget(screen_cls(name=name))
        return self.sm

    def on_start(self):
        if platform in ("android", "ios") or not local_server.is_local(self.api.base_url):
            # Бесплатный Render засыпает без запросов: первый запрос будит его до минуты
            self.server_info = f"Сервер: {self.api.base_url} · просыпается, это до минуты..."

            def awake(_result=None) -> None:
                self._update_server_info(started=False)
                self._restore_session()

            run_async(self.api.wake, awake, lambda _e: awake())
            return
        # На компьютере: при необходимости поднимаем встроенный сервер, потом восстанавливаем сессию
        self.server_info = f"Сервер: {self.api.base_url} · запускается..."

        def started(is_embedded: bool) -> None:
            self._update_server_info(started=is_embedded)
            self._restore_session()

        run_async(lambda: local_server.start_if_needed(self.api.base_url), started,
                  lambda _e: started(False))

    def _restore_session(self) -> None:
        # Если в прошлый раз не вышли из аккаунта, восстанавливаем сессию по refresh-токену
        if self.store.exists("auth"):
            self.api.refresh_token = self.store.get("auth").get("refresh_token")
            if self.api.refresh_token:
                run_async(self.api.restore_session, self.on_logged_in, lambda _e: self._clear_session())

    # ---------- адрес сервера ----------

    def _saved_api_url(self) -> str:
        try:
            return self.store.get("server").get("url") or API_URL
        except Exception:
            return API_URL

    def _update_server_info(self, started: bool) -> None:
        info = f"Сервер: {self.api.base_url}"
        if started:
            ip = local_server.lan_ip()
            info += " · встроенный"
            if ip:
                info += f"\nДля телефона в той же Wi-Fi сети: http://{ip}:{local_server.port_of(self.api.base_url)}"
        self.server_info = info

    def ask_server_url(self) -> None:
        prompt(
            "Адрес сервера",
            f"Пусто — облако ({CLOUD_URL}). Свой компьютер: http://127.0.0.1:8000, "
            "телефон в той же Wi-Fi сети: http://IP-компьютера:8000.",
            self.api.base_url, self.set_server_url, ok_text="Сохранить",
        )

    def set_server_url(self, url: str) -> None:
        url = url.strip().rstrip("/") or CLOUD_URL
        if "://" not in url:
            url = "http://" + url
        host = url.split("://", 1)[1]
        # порт по умолчанию 8000 — только для локального сервера (IP или localhost), не для облака
        if url.startswith("http://") and ":" not in host and (host == "localhost" or host[0].isdigit()):
            url += ":8000"
        self.api.base_url = url
        try:
            self.store.put("server", url=url)
        except Exception:
            pass
        self._clear_session()
        self._update_server_info(started=False)
        notify(f"Адрес сервера: {url}")

    # ---------- навигация ----------

    def goto(self, name: str, direction: str = "left", **kwargs) -> None:
        screen = self.sm.get_screen(name)
        if kwargs and hasattr(screen, "prepare"):
            screen.prepare(**kwargs)
        self.sm.transition.direction = direction
        self.sm.current = name

    def _on_keyboard(self, _window, key, *_args):
        if key == 27:  # Esc на компьютере / «Назад» на Android
            if self.sm.current in ("login", "main"):
                return False  # стандартное поведение: выход
            self.sm.current_screen.go_back()
            return True
        return False

    # ---------- тема ----------

    def _saved_theme(self) -> str:
        try:
            return self.store.get("theme").get("name", "light")
        except Exception:
            return "light"

    def toggle_theme(self) -> None:
        name = "light" if theme.P.is_dark else "dark"
        theme.P.apply(name)   # KV-разметка перекрашивается сама: цвета привязаны к свойствам P
        try:
            self.store.put("theme", name=name)
        except Exception:
            pass  # не смогли запомнить выбор: не критично

    # ---------- сессия ----------

    def has_perm(self, code: str) -> bool:
        return code in self.permissions

    def set_user(self, me: dict) -> None:
        self.user = me
        self.username = me["username"]
        self.role = me["role"]
        self.permissions = me.get("permissions", [])
        self.is_guest = False

    def on_logged_in(self, me: dict) -> None:
        self.set_user(me)
        self.goto("main")

    def enter_as_guest(self) -> None:
        self._clear_session()
        self.goto("main")

    def leave_guest_mode(self) -> None:
        self.goto("login", direction="right", reset=True)

    def _clear_session(self) -> None:
        self.api.clear_tokens()
        self.user = None
        self.username = "Гость"
        self.role = "guest"
        self.permissions = []
        self.is_guest = True

    def _save_refresh_token(self, refresh_token: str | None) -> None:
        try:
            if refresh_token:
                self.store.put("auth", refresh_token=refresh_token)
            elif self.store.exists("auth"):
                self.store.delete("auth")
        except Exception:
            pass  # не смогли сохранить сессию на диск: не критично

    def logout(self) -> None:
        def do_logout():
            def finish(*_args):
                self._clear_session()
                self.goto("login", direction="right", reset=True)
                notify("Вы вышли из аккаунта")
            run_async(self.api.logout, finish, finish)
        confirm("Выйти из аккаунта?", do_logout, yes_text="Выйти")

    # ---------- ошибки ----------

    def show_error(self, err: ApiError) -> None:
        if err.status == 401 and self.sm.current not in AUTH_SCREENS and not self.is_guest:
            self._clear_session()
            self.goto("login", direction="right", reset=True)
            notify("Сессия истекла. Войдите снова.", "info")
            return
        notify(err.detail, "error")


if __name__ == "__main__":
    NecropolisApp().run()
