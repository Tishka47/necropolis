from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import escape_markup, get_hex_from_color

import theme
from screens.base import BaseScreen
from services.async_task import run_async
from utils import ROLE_LABELS, fmt_date
from widgets.dialogs import confirm, notify

ROLES = ("user", "moderator", "admin")
ROLE_CODES = {ROLE_LABELS[code]: code for code in ROLES}


def esc(text) -> str:
    return escape_markup(str(text or ""))


class AdminScreen(BaseScreen):
    """Администрирование: пользователи (роль, блокировка) и места памяти.
    Разделы показываются по разрешениям: user:manage и location:manage."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._loc_name = self._loc_address = self._loc_description = None

    def on_pre_enter(self, *_args) -> None:
        self.ids.content.clear_widgets()
        self.ids.content.add_widget(Factory.MutedLabel(text="Загрузка..."))
        self.load()

    def load(self) -> None:
        api = self.app.api
        can_users = self.app.has_perm("user:manage")

        def task():
            return (api.list_users() if can_users else None), api.list_locations()

        run_async(task, self._render, self.app.show_error)

    # ---------- отрисовка ----------

    def _render(self, result) -> None:
        users, locations = result
        box = self.ids.content
        box.clear_widgets()
        if users is not None:
            self._render_users(box.add_widget, users)
        if self.app.has_perm("location:manage"):
            self._render_locations(box.add_widget, locations)

    def _render_users(self, add, users: list) -> None:
        add(Factory.SectionLabel(text=f"Пользователи ({len(users)})"))
        me_id = self.app.user["id"] if self.app.user else None
        for i, user in enumerate(users):
            card = Factory.Card()
            card.rule = i > 0
            name = f"[b]{esc(user['username'])}[/b]"
            if user["id"] == me_id:
                name += "  (это вы)"
            card.add_widget(Factory.AppLabel(text=name))
            if user["is_active"]:
                state = "активен"
            else:
                state = f"[color={get_hex_from_color(theme.P.DANGER)}]заблокирован[/color]"
            card.add_widget(Factory.MutedLabel(
                text=f"{esc(user['email'])}\n"
                     f"{ROLE_LABELS.get(user['role'], user['role'])}  ·  {state}  ·  "
                     f"с {fmt_date(user['created_at'])}"
            ))
            if user["id"] != me_id:
                card.add_widget(self._user_controls(user))
            add(card)

    def _user_controls(self, user: dict) -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(10))
        spinner = Factory.AppSpinner(
            text=ROLE_LABELS[user["role"]], values=[ROLE_LABELS[r] for r in ROLES], height=dp(42),
        )
        spinner.bind(text=lambda _inst, label, u=user: self.change_role(u, label))
        row.add_widget(spinner)
        if user["is_active"]:
            button = Factory.DangerButton(text="Заблокировать", height=dp(42))
        else:
            button = Factory.SecondaryButton(text="Разблокировать", height=dp(42))
        button.size_hint_x = None
        button.width = dp(150)
        button.bind(on_release=lambda *_a, u=user: self.toggle_active(u))
        row.add_widget(button)
        return row

    def _render_locations(self, add, locations: list) -> None:
        add(Factory.SectionLabel(text=f"Места памяти ({len(locations)})"))
        if not locations:
            add(Factory.MutedLabel(text="Мест пока нет"))
        for loc in locations:
            address = f"\n[color={get_hex_from_color(theme.P.MUTED)}]{esc(loc['address'])}[/color]" if loc["address"] else ""
            add(Factory.AppLabel(text=f"• {esc(loc['name'])}{address}"))

        add(Factory.MutedLabel(text="Добавить место"))
        self._loc_name = Factory.AppInput(hint_text="Название, например «Ваганьковское кладбище»")
        self._loc_address = Factory.AppInput(hint_text="Адрес")
        self._loc_description = Factory.AppInput(hint_text="Описание (необязательно)")
        button = Factory.SecondaryButton(text="Добавить место")
        button.bind(on_release=lambda *_: self.add_location())
        for widget in (self._loc_name, self._loc_address, self._loc_description, button):
            add(widget)

    # ---------- действия ----------

    def change_role(self, user: dict, label: str) -> None:
        role = ROLE_CODES.get(label)
        if not role or role == user["role"]:
            return

        def done(_result):
            notify(f"{user['username']}: роль «{label}»")
            self.load()

        run_async(lambda: self.app.api.change_role(user["id"], role), done, self._on_error)

    def toggle_active(self, user: dict) -> None:
        block = user["is_active"]

        def do():
            def done(_result):
                notify(f"{user['username']} заблокирован" if block else f"{user['username']} разблокирован")
                self.load()
            run_async(lambda: self.app.api.set_user_active(user["id"], not block), done, self._on_error)

        if block:
            confirm(f"Заблокировать {user['username']}? Он не сможет войти, "
                    "все его сессии будут завершены.", do, yes_text="Заблокировать")
        else:
            do()

    def add_location(self) -> None:
        name = self._loc_name.text.strip()
        if len(name) < 2:
            notify("Введите название места (минимум 2 символа)", "error")
            return
        payload = {
            "name": name,
            "address": self._loc_address.text.strip(),
            "description": self._loc_description.text.strip(),
        }

        def done(_result):
            notify("Место добавлено")
            self.load()

        run_async(lambda: self.app.api.create_location(payload), done)

    def _on_error(self, err) -> None:
        self.app.show_error(err)
        self.load()  # вернуть переключатель роли в актуальное состояние
