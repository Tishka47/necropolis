from kivy.utils import escape_markup

from screens.base import BaseScreen
from services.async_task import run_async
from utils import ROLE_LABELS, fmt_date
from widgets.dialogs import notify


class ProfileScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.me: dict | None = None

    def on_pre_enter(self, *_args) -> None:
        self.load()

    def load(self) -> None:
        run_async(self.app.api.me, self._render)

    def _render(self, me: dict) -> None:
        self.me = me
        self.app.set_user(me)
        self.ids.name_label.text = escape_markup(me["username"])
        self.ids.info_label.text = (
            f"{escape_markup(me['email'])}\n"
            f"Роль: {ROLE_LABELS.get(me['role'], me['role'])}\n"
            f"С нами с {fmt_date(me['created_at'])}"
        )
        self.ids.email.text = me["email"]
        self.ids.current_password.text = ""
        self.ids.new_password.text = ""

    # ---------- данные аккаунта ----------

    def save_profile(self) -> None:
        payload = {}
        email = self.ids.email.text.strip()
        if email and email != self.me["email"]:
            if "@" not in email:
                notify("Введите корректный email", "error")
                return
            payload["email"] = email
        new_password = self.ids.new_password.text
        if new_password:
            if len(new_password) < 6:
                notify("Новый пароль должен быть не короче 6 символов", "error")
                return
            if not self.ids.current_password.text:
                notify("Для смены пароля введите текущий пароль", "error")
                return
            payload["new_password"] = new_password
            payload["current_password"] = self.ids.current_password.text
        if not payload:
            notify("Вы ничего не изменили", "info")
            return
        run_async(lambda: self.app.api.update_me(payload), self._on_saved)

    def _on_saved(self, me: dict) -> None:
        notify("Профиль обновлён")
        self._render(me)
