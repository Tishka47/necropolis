import re

from kivy.properties import BooleanProperty

from screens.base import BaseScreen
from services.async_task import run_async
from widgets.dialogs import notify

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginScreen(BaseScreen):
    busy = BooleanProperty(False)

    def prepare(self, **_kwargs) -> None:
        self.ids.password.text = ""

    def do_login(self) -> None:
        login = self.ids.login.text.strip()
        password = self.ids.password.text
        if not login or not password:
            notify("Введите логин и пароль", "error")
            return

        api = self.app.api

        def task():
            api.login(login, password)
            return api.me()

        self.busy = True
        run_async(task, self._on_success, self._on_error)

    def _on_success(self, me: dict) -> None:
        self.busy = False
        self.app.on_logged_in(me)
        notify(f"Добро пожаловать, {me['username']}!")

    def _on_error(self, err) -> None:
        self.busy = False
        self.app.show_error(err)


class RegisterScreen(BaseScreen):
    busy = BooleanProperty(False)

    def do_register(self) -> None:
        username = self.ids.username.text.strip()
        email = self.ids.email.text.strip()
        password = self.ids.password.text
        password2 = self.ids.password2.text

        if not USERNAME_RE.match(username):
            notify("Логин: 3–50 символов, латиница, цифры, _ . -", "error")
            return
        if not EMAIL_RE.match(email):
            notify("Введите корректный email", "error")
            return
        if len(password) < 6:
            notify("Пароль должен быть не короче 6 символов", "error")
            return
        if password != password2:
            notify("Пароли не совпадают", "error")
            return

        api = self.app.api

        def task():
            api.register(username, email, password)
            api.login(username, password)
            return api.me()

        self.busy = True
        run_async(task, self._on_success, self._on_error)

    def _on_success(self, me: dict) -> None:
        self.busy = False
        for field in ("username", "email", "password", "password2"):
            self.ids[field].text = ""
        self.app.on_logged_in(me)
        notify("Регистрация прошла успешно")

    def _on_error(self, err) -> None:
        self.busy = False
        self.app.show_error(err)
