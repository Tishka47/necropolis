import webbrowser

from kivy.factory import Factory
from kivy.metrics import dp, sp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import escape_markup, get_hex_from_color

import theme
from screens.base import BaseScreen
from services.async_task import run_async
from utils import MATERIAL_TYPES, STATUS_LABELS, fmt_date, life_dates
from widgets.dialogs import confirm, notify

MATERIAL_CODES = {label: code for code, label in MATERIAL_TYPES.items()}


def esc(text) -> str:
    return escape_markup(str(text or ""))


class DetailScreen(BaseScreen):
    """Просмотр записи: данные, места, биография, материалы, воспоминания, действия."""
    screen_title = StringProperty("Страница памяти")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.memorial_id = 0
        self.memorial: dict | None = None
        self._mat_type = self._mat_title = self._mat_url = self._comment_input = None

    def prepare(self, memorial_id: int, back_target: str = "list", **_kwargs) -> None:
        self.memorial_id = memorial_id
        self.back_target = back_target
        self.memorial = None
        self.screen_title = "Страница памяти"
        self.ids.content.clear_widgets()
        self.ids.content.add_widget(Factory.MutedLabel(text="Загрузка..."))

    def on_pre_enter(self, *_args) -> None:
        if self.memorial_id:
            self.load()

    def load(self) -> None:
        memorial_id = self.memorial_id
        api = self.app.api

        def task():
            return (api.get_memorial(memorial_id), api.list_materials(memorial_id),
                    api.list_comments(memorial_id))

        run_async(task, self._render, self._on_load_error)

    def _on_load_error(self, err) -> None:
        self.app.show_error(err)
        if err.status == 404:
            self.go_back()

    # ---------- отрисовка ----------

    @staticmethod
    def _row(items, height=dp(46)) -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=height, spacing=dp(10))
        for widget_cls, text, callback in items:
            button = getattr(Factory, widget_cls)(text=text, height=height)
            button.bind(on_release=lambda *_a, cb=callback: cb())
            row.add_widget(button)
        return row

    def _render(self, result) -> None:
        memorial, materials, comments = result
        self.memorial = memorial
        self.screen_title = memorial["full_name"]
        app = self.app
        me_id = app.user["id"] if app.user else None
        box = self.ids.content
        box.clear_widgets()
        add = box.add_widget

        # Шапка
        status_color = get_hex_from_color(theme.P.status_color(memorial["status"]))
        header = Factory.HeaderBlock()
        header.add_widget(Factory.TitleLabel(text=esc(memorial["full_name"]), halign="center"))
        header.add_widget(Factory.AppLabel(
            text=f"[i]{life_dates(memorial['birth_date'], memorial['death_date'])}[/i]",
            font_name=theme.SERIF, font_size=sp(17), halign="center",
        ))
        header.add_widget(Factory.MutedLabel(
            text=f"Статус: [color={status_color}]{STATUS_LABELS.get(memorial['status'], '')}[/color]"
                 f"   ·   автор: {esc(memorial['creator']['username'])}",
            halign="center",
        ))
        add(header)

        # Действия автора
        actions = []
        if memorial["can_edit"]:
            actions.append(("SecondaryButton", "Редактировать", self.edit))
        if memorial["can_delete"]:
            actions.append(("DangerButton", "Удалить", self.ask_delete))
        if actions:
            add(self._row(actions))

        # Модерация
        if memorial["can_moderate"]:
            moderation = []
            if memorial["status"] != "approved":
                moderation.append(("AppButton", "Опубликовать", lambda: self.set_status("approved")))
            if memorial["status"] != "rejected":
                moderation.append(("DangerButton", "Отклонить", lambda: self.set_status("rejected")))
            if moderation:
                add(Factory.SectionLabel(text="Модерация"))
                add(self._row(moderation))

        # Места памяти
        if memorial["locations"]:
            add(Factory.SectionLabel(text="Места памяти"))
            for loc in memorial["locations"]:
                address = f"\n[color={get_hex_from_color(theme.P.MUTED)}]{esc(loc['address'])}[/color]" if loc["address"] else ""
                add(Factory.AppLabel(text=f"• {esc(loc['name'])}{address}"))

        # Биография
        add(Factory.SectionLabel(text="Биография"))
        add(Factory.AppLabel(text=esc(memorial["biography"]) or "[i]Биография пока не добавлена[/i]"))

        self._render_materials(add, memorial, materials, me_id)
        self._render_comments(add, memorial, comments, me_id)

    def _render_materials(self, add, memorial, materials, me_id) -> None:
        add(Factory.SectionLabel(text=f"Материалы ({len(materials)})"))
        if not materials:
            add(Factory.MutedLabel(text="Материалов пока нет"))
        for i, material in enumerate(materials):
            card = Factory.Card()
            card.rule = i > 0
            type_label = MATERIAL_TYPES.get(material["type"], material["type"])
            card.add_widget(Factory.AppLabel(
                text=f"[b]{esc(material['title'])}[/b]   "
                     f"[color={get_hex_from_color(theme.P.ACCENT)}]{type_label}[/color]"
            ))
            if material["file_url"]:
                card.add_widget(Factory.MutedLabel(text=esc(material["file_url"])))
            buttons = []
            url = material["file_url"]
            if url.startswith(("http://", "https://")):
                buttons.append(("SecondaryButton", "Открыть", lambda u=url: webbrowser.open(u)))
            if me_id and (material["author"]["id"] == me_id or memorial["can_edit"]
                          or self.app.has_perm("material:delete_any")):
                buttons.append(("DangerButton", "Удалить",
                                lambda mid=material["id"]: self.ask_delete_material(mid)))
            if buttons:
                card.add_widget(self._row(buttons, height=dp(40)))
            add(card)

        if memorial["can_edit"]:
            add(Factory.MutedLabel(text="Добавить материал"))
            self._mat_type = Factory.AppSpinner(text=MATERIAL_TYPES["photo"], values=list(MATERIAL_TYPES.values()))
            self._mat_title = Factory.AppInput(hint_text="Название, например «Фото 1950 года»")
            self._mat_url = Factory.AppInput(hint_text="Ссылка на файл или текст")
            button = Factory.SecondaryButton(text="Добавить материал")
            button.bind(on_release=lambda *_: self.add_material())
            for widget in (self._mat_type, self._mat_title, self._mat_url, button):
                add(widget)

    def _render_comments(self, add, memorial, comments, me_id) -> None:
        add(Factory.SectionLabel(text=f"Воспоминания ({len(comments)})"))
        if not comments:
            add(Factory.MutedLabel(text="Пока никто не поделился воспоминаниями"))
        for i, comment in enumerate(comments):
            card = Factory.Card()
            card.rule = i > 0
            card.add_widget(Factory.MutedLabel(
                text=f"{esc(comment['author']['username'])}  ·  {fmt_date(comment['created_at'])}"
            ))
            card.add_widget(Factory.AppLabel(text=esc(comment["text"])))
            if me_id and (comment["author"]["id"] == me_id or self.app.has_perm("comment:delete_any")):
                card.add_widget(self._row(
                    [("DangerButton", "Удалить", lambda cid=comment["id"]: self.ask_delete_comment(cid))],
                    height=dp(40),
                ))
            add(card)

        if self.app.is_guest:
            add(Factory.MutedLabel(text="Войдите, чтобы оставить воспоминание"))
        elif memorial["status"] == "approved":
            self._comment_input = Factory.AreaInput(hint_text="Поделитесь воспоминанием...")
            button = Factory.AppButton(text="Отправить")
            button.bind(on_release=lambda *_: self.add_comment())
            add(self._comment_input)
            add(button)

    # ---------- действия ----------

    def edit(self) -> None:
        self.app.goto("form", memorial=self.memorial, back_target="detail")

    def ask_delete(self) -> None:
        confirm(f"Удалить страницу «{self.memorial['full_name']}»? "
                "Материалы и воспоминания тоже будут удалены. Отменить это нельзя.", self._delete)

    def _delete(self) -> None:
        memorial_id = self.memorial_id
        run_async(lambda: self.app.api.delete_memorial(memorial_id), self._on_deleted)

    def _on_deleted(self, _result) -> None:
        notify("Страница удалена")
        self.memorial_id = 0
        self.go_back()

    def set_status(self, status: str) -> None:
        memorial_id = self.memorial_id

        def done(_result):
            notify("Страница опубликована" if status == "approved" else "Страница отклонена")
            self.load()

        run_async(lambda: self.app.api.set_memorial_status(memorial_id, status), done)

    def add_material(self) -> None:
        title = self._mat_title.text.strip()
        if not title:
            notify("Введите название материала", "error")
            return
        payload = {
            "type": MATERIAL_CODES.get(self._mat_type.text, "photo"),
            "title": title,
            "file_url": self._mat_url.text.strip(),
        }
        memorial_id = self.memorial_id

        def done(_result):
            notify("Материал добавлен")
            self.load()

        run_async(lambda: self.app.api.add_material(memorial_id, payload), done)

    def ask_delete_material(self, material_id: int) -> None:
        def do():
            def done(_result):
                notify("Материал удалён")
                self.load()
            run_async(lambda: self.app.api.delete_material(material_id), done)
        confirm("Удалить этот материал?", do)

    def add_comment(self) -> None:
        text = self._comment_input.text.strip()
        if not text:
            notify("Напишите текст воспоминания", "error")
            return
        memorial_id = self.memorial_id

        def done(_result):
            notify("Спасибо, воспоминание сохранено")
            self.load()

        run_async(lambda: self.app.api.add_comment(memorial_id, text), done)

    def ask_delete_comment(self, comment_id: int) -> None:
        def do():
            def done(_result):
                notify("Воспоминание удалено")
                self.load()
            run_async(lambda: self.app.api.delete_comment(comment_id), done)
        confirm("Удалить это воспоминание?", do)
