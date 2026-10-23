from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

from screens.base import BaseScreen
from services.async_task import run_async
from utils import STATUS_LABELS, life_years

FILTERS = {
    "Все статусы": None,
    "Опубликованные": "approved",
    "На модерации": "pending",
    "Отклонённые": "rejected",
}
TITLES = {"all": "Каталог памяти", "mine": "Мои страницы", "moderation": "Модерация"}


class MemorialItem(ButtonBehavior, BoxLayout):
    """Строка списка. Поля заполняются из словаря в RecycleView.data."""
    memorial_id = NumericProperty(0)
    title = StringProperty("")
    subtitle = StringProperty("")
    status = StringProperty("")
    status_text = StringProperty("")

    def on_release(self):
        from kivy.app import App
        App.get_running_app().goto("detail", memorial_id=self.memorial_id, back_target="list")


class ListScreen(BaseScreen):
    mode = StringProperty("all")
    screen_title = StringProperty(TITLES["all"])
    info_text = StringProperty("")
    filter_values = ListProperty(list(FILTERS))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._suppress_filter = False

    def prepare(self, mode: str = "all", **_kwargs) -> None:
        self.mode = mode
        self.screen_title = TITLES.get(mode, TITLES["all"])
        self._suppress_filter = True
        self.ids.search.text = ""
        self.ids.status_filter.text = "На модерации" if mode == "moderation" else "Все статусы"
        self._suppress_filter = False
        self.ids.rv.data = []

    def on_pre_enter(self, *_args) -> None:
        self.load()

    def on_filter_changed(self) -> None:
        if not self._suppress_filter:
            self.load()

    def reset_filters(self) -> None:
        self.prepare(self.mode)
        self.load()

    def load(self) -> None:
        params = {}
        query = self.ids.search.text.strip()
        if query:
            params["q"] = query
        status = FILTERS.get(self.ids.status_filter.text)
        if status:
            params["status"] = status
        if self.mode == "mine":
            params["mine"] = "true"

        self.info_text = "Загрузка..."
        run_async(lambda: self.app.api.list_memorials(params), self._show, self._on_error)

    def _show(self, items: list) -> None:
        self.ids.rv.data = [
            {
                "memorial_id": m["id"],
                "title": m["full_name"],
                "subtitle": f"{life_years(m['birth_date'], m['death_date'])}  ·  {m['creator']['username']}",
                "status": m["status"],
                "status_text": STATUS_LABELS.get(m["status"], m["status"]).upper(),
            }
            for m in items
        ]
        self.info_text = f"Найдено: {len(items)}" if items else "Ничего не найдено"

    def _on_error(self, err) -> None:
        self.info_text = "Не удалось загрузить список"
        self.app.show_error(err)
