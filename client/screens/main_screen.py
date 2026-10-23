from kivy.factory import Factory
from kivy.utils import escape_markup

import theme
from screens.base import BaseScreen
from utils import ROLE_LABELS


class MainScreen(BaseScreen):
    """Главный экран. Меню собирается по правам пользователя: гость, автор, модератор."""

    def on_pre_enter(self, *_args) -> None:
        app = self.app
        self.ids.greeting.text = f"Здравствуйте, {escape_markup(app.username)}"
        self.ids.role_label.text = ROLE_LABELS.get(app.role, app.role)

        menu = self.ids.menu
        menu.clear_widgets()

        def add(widget_cls: str, text: str, callback) -> None:
            button = getattr(Factory, widget_cls)(text=text)
            button.bind(on_release=lambda *_: callback())
            menu.add_widget(button)

        def toggle_theme() -> None:
            app.toggle_theme()
            self.on_pre_enter()  # обновить подпись пункта

        theme_label = "Светлая тема" if theme.P.is_dark else "Тёмная тема"

        add("MenuRow", "Каталог памяти", lambda: app.goto("list", mode="all"))
        if app.is_guest:
            add("MenuRow", "Войти или зарегистрироваться", app.leave_guest_mode)
            add("MenuRow", theme_label, toggle_theme)
            return

        add("MenuRow", "Мои страницы", lambda: app.goto("list", mode="mine"))
        if app.has_perm("memorial:create"):
            add("MenuRow", "Создать страницу", lambda: app.goto("form", memorial=None, back_target="main"))
        if app.has_perm("memorial:moderate"):
            add("MenuRow", "Модерация", lambda: app.goto("list", mode="moderation"))
        if app.has_perm("user:manage") or app.has_perm("location:manage"):
            add("MenuRow", "Администрирование", lambda: app.goto("admin"))
        add("MenuRow", "Профиль", lambda: app.goto("profile"))
        add("MenuRow", theme_label, toggle_theme)
        add("MenuRowDanger", "Выйти", app.logout)
