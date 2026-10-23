from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen


class BaseScreen(Screen):
    """Общий предок экранов: доступ к приложению и кнопка «Назад»."""
    back_target = StringProperty("main")

    @property
    def app(self):
        return App.get_running_app()

    def go_back(self) -> None:
        self.app.goto(self.back_target, direction="right")
