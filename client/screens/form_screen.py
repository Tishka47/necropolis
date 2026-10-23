from datetime import date

from kivy.factory import Factory
from kivy.properties import StringProperty

from screens.base import BaseScreen
from services.async_task import run_async
from utils import fmt_date, parse_date
from widgets.dialogs import notify


class FormScreen(BaseScreen):
    """Один экран и для создания, и для редактирования записи."""
    screen_title = StringProperty("Новая страница")
    save_text = StringProperty("Создать")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.edit_id: int | None = None
        self.selected_locations: set[int] = set()
        self._detail_back = "list"

    def prepare(self, memorial: dict | None = None, back_target: str = "main", **_kwargs) -> None:
        self.back_target = back_target
        ids = self.ids
        if memorial:
            self.edit_id = memorial["id"]
            self.screen_title = "Редактирование"
            self.save_text = "Сохранить изменения"
            ids.full_name.text = memorial["full_name"]
            ids.birth_date.text = fmt_date(memorial["birth_date"])
            ids.death_date.text = fmt_date(memorial["death_date"])
            ids.biography.text = memorial["biography"]
            self.selected_locations = {loc["id"] for loc in memorial["locations"]}
            self._detail_back = self.app.sm.get_screen("detail").back_target
        else:
            self.edit_id = None
            self.screen_title = "Новая страница"
            self.save_text = "Создать"
            for field in ("full_name", "birth_date", "death_date", "biography"):
                ids[field].text = ""
            self.selected_locations = set()
        ids.locations_box.clear_widgets()
        run_async(self.app.api.list_locations, self._render_locations)

    def _render_locations(self, locations: list) -> None:
        box = self.ids.locations_box
        box.clear_widgets()
        if not locations:
            box.add_widget(Factory.MutedLabel(text="Места памяти пока не добавлены"))
        for loc in locations:
            chip = Factory.ChipToggle(text=loc["name"],
                                      state="down" if loc["id"] in self.selected_locations else "normal")
            chip.bind(state=lambda _inst, value, lid=loc["id"]: self._toggle_location(lid, value))
            box.add_widget(chip)

    def _toggle_location(self, location_id: int, state: str) -> None:
        if state == "down":
            self.selected_locations.add(location_id)
        else:
            self.selected_locations.discard(location_id)

    def save(self) -> None:
        ids = self.ids
        full_name = " ".join(ids.full_name.text.split())
        if len(full_name) < 2:
            notify("Укажите ФИО (минимум 2 символа)", "error")
            return
        try:
            birth = parse_date(ids.birth_date.text)
            death = parse_date(ids.death_date.text)
        except ValueError as exc:
            notify(str(exc), "error")
            return
        if birth and death and date.fromisoformat(death) < date.fromisoformat(birth):
            notify("Дата смерти не может быть раньше даты рождения", "error")
            return

        payload = {
            "full_name": full_name,
            "birth_date": birth,
            "death_date": death,
            "biography": ids.biography.text.strip(),
            "location_ids": sorted(self.selected_locations),
        }
        api = self.app.api
        if self.edit_id:
            edit_id = self.edit_id
            run_async(lambda: api.update_memorial(edit_id, payload), self._on_saved)
        else:
            run_async(lambda: api.create_memorial(payload), self._on_saved)

    def _on_saved(self, memorial: dict) -> None:
        pending = memorial["status"] == "pending"
        message = "Страница сохранена"
        if pending:
            message += " и отправлена на модерацию"
        notify(message)
        back = self._detail_back if self.edit_id else "main"
        self.app.goto("detail", memorial_id=memorial["id"], back_target=back, direction="right")
