"""Сообщения об успехе/ошибке, окно подтверждения и окно ввода в едином стиле."""
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView

import theme

_KINDS = {  # цвет берётся из палитры в момент показа: тема могла смениться
    "success": ("Готово", "SUCCESS"),
    "error": ("Ошибка", "DANGER"),
    "info": ("Внимание", "INFO"),
}


def _build(title: str, text: str, accent) -> tuple[ModalView, BoxLayout]:
    overlay = (0, 0, 0, 0.6) if theme.P.is_dark else list(theme.P.TEXT[:3]) + [0.45]
    view = ModalView(
        size_hint=(0.88, None), height=dp(160),
        background="", background_color=(0, 0, 0, 0), overlay_color=overlay,
    )
    card = Factory.DialogCard()
    card.accent = accent
    title_label = Factory.DialogTitle(text=title)
    title_label.color = accent  # после создания: правило KV привязывает color к палитре и перебило бы kwargs
    card.add_widget(title_label)
    card.add_widget(Factory.DialogText(text=text))
    view.add_widget(card)
    card.bind(height=lambda _inst, h: setattr(view, "height", h))
    return view, card


def notify(text: str, kind: str = "success") -> None:
    title, color_name = _KINDS.get(kind, _KINDS["info"])
    view, card = _build(title, text, getattr(theme.P, color_name))
    button = Factory.AppButton(text="Понятно")
    button.bind(on_release=lambda *_: view.dismiss())
    card.add_widget(button)
    view.open()
    if kind == "success":
        Clock.schedule_once(lambda _dt: view.dismiss(), 1.8)


def confirm(text: str, on_yes, yes_text: str = "Удалить", danger: bool = True,
            title: str = "Подтверждение") -> None:
    view, card = _build(title, text, theme.P.DANGER if danger else theme.P.ACCENT)
    row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
    no_button = Factory.SecondaryButton(text="Отмена")
    yes_button = Factory.DangerButton(text=yes_text) if danger else Factory.AppButton(text=yes_text)

    def _yes(*_):
        view.dismiss()
        on_yes()

    no_button.bind(on_release=lambda *_: view.dismiss())
    yes_button.bind(on_release=_yes)
    row.add_widget(no_button)
    row.add_widget(yes_button)
    card.add_widget(row)
    view.open()


def prompt(title: str, text: str, initial: str, on_ok, ok_text: str = "OK") -> None:
    """Окно с одним полем ввода. on_ok получает введённый текст."""
    view, card = _build(title, text, theme.P.ACCENT)
    field = Factory.AppInput(text=initial)
    card.add_widget(field)
    row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
    cancel_button = Factory.SecondaryButton(text="Отмена")
    ok_button = Factory.AppButton(text=ok_text)

    def _ok(*_):
        view.dismiss()
        on_ok(field.text)

    cancel_button.bind(on_release=lambda *_: view.dismiss())
    ok_button.bind(on_release=_ok)
    field.bind(on_text_validate=_ok)
    row.add_widget(cancel_button)
    row.add_widget(ok_button)
    card.add_widget(row)
    view.open()
