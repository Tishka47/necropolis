"""Единая палитра и шрифты всех экранов. Две темы: светлая («бумага и чернила», как в книге памяти)
и тёмная (тёплая, в тех же тонах). Цвета лежат в свойствах объекта P, поэтому разметка KV
перекрашивается сама при смене темы: P.apply("dark")."""
import os

from kivy.core.text import LabelBase
from kivy.event import EventDispatcher
from kivy.properties import ColorProperty, StringProperty

THEMES = {
    "light": {
        "BG": (0.957, 0.945, 0.918, 1),        # бумага
        "SURFACE": (0.925, 0.910, 0.875, 1),   # чуть темнее бумаги: подложки, нажатое состояние
        "SURFACE_2": (0.890, 0.871, 0.827, 1),
        "RULE": (0.800, 0.773, 0.710, 1),      # тонкие линии-разделители
        "TEXT": (0.141, 0.129, 0.114, 1),      # чернила
        "MUTED": (0.455, 0.427, 0.384, 1),
        "ACCENT": (0.420, 0.169, 0.149, 1),    # тёмно-красный, как сургуч
        "DANGER": (0.557, 0.231, 0.196, 1),
        "SUCCESS": (0.306, 0.420, 0.227, 1),
        "INFO": (0.271, 0.357, 0.455, 1),
        "PENDING": (0.627, 0.471, 0.173, 1),
    },
    "dark": {
        "BG": (0.106, 0.102, 0.090, 1),
        "SURFACE": (0.149, 0.141, 0.129, 1),
        "SURFACE_2": (0.200, 0.190, 0.173, 1),
        "RULE": (0.300, 0.284, 0.255, 1),
        "TEXT": (0.910, 0.890, 0.851, 1),      # пергамент
        "MUTED": (0.620, 0.596, 0.553, 1),
        "ACCENT": (0.784, 0.451, 0.408, 1),
        "DANGER": (0.851, 0.467, 0.420, 1),
        "SUCCESS": (0.561, 0.702, 0.475, 1),
        "INFO": (0.541, 0.659, 0.800, 1),
        "PENDING": (0.851, 0.702, 0.420, 1),
    },
}


class Palette(EventDispatcher):
    name = StringProperty("light")
    BG = ColorProperty(THEMES["light"]["BG"])
    SURFACE = ColorProperty(THEMES["light"]["SURFACE"])
    SURFACE_2 = ColorProperty(THEMES["light"]["SURFACE_2"])
    RULE = ColorProperty(THEMES["light"]["RULE"])
    TEXT = ColorProperty(THEMES["light"]["TEXT"])
    MUTED = ColorProperty(THEMES["light"]["MUTED"])
    ACCENT = ColorProperty(THEMES["light"]["ACCENT"])
    ON_ACCENT = ColorProperty(THEMES["light"]["BG"])   # текст на тёмной/акцентной кнопке = цвет фона
    DANGER = ColorProperty(THEMES["light"]["DANGER"])
    SUCCESS = ColorProperty(THEMES["light"]["SUCCESS"])
    INFO = ColorProperty(THEMES["light"]["INFO"])
    PENDING = ColorProperty(THEMES["light"]["PENDING"])

    @property
    def is_dark(self) -> bool:
        return self.name == "dark"

    def apply(self, name: str) -> None:
        colors = THEMES.get(name, THEMES["light"])
        for key, value in colors.items():
            setattr(self, key, value)
        self.ON_ACCENT = colors["BG"]
        self.name = name if name in THEMES else "light"

    def status_color(self, status: str):
        return {"approved": self.SUCCESS, "pending": self.PENDING, "rejected": self.DANGER}.get(status, self.MUTED)


P = Palette()

SERIF = "PTSerif"

_FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def register_fonts() -> None:
    """PT Sans становится шрифтом по умолчанию (подменяем Roboto), PT Serif — для заголовков."""
    for name, family in (("Roboto", "PTSans"), (SERIF, "PTSerif")):
        LabelBase.register(
            name,
            os.path.join(_FONTS, f"{family}-Regular.ttf"),
            os.path.join(_FONTS, f"{family}-Italic.ttf"),
            os.path.join(_FONTS, f"{family}-Bold.ttf"),
            os.path.join(_FONTS, f"{family}-BoldItalic.ttf"),
        )
