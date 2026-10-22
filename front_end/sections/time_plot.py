"""Result plot section: shows the run time plot once the pipeline completes."""
from pathlib import Path
from nicegui import app, ui
from front_end.components.text_comp import text


class TimePlot:
    def __init__(self) -> None:
        self._card = ui.card().classes("w-full rounded-xl shadow-md p-6 gap-3")
        with self._card:
            text("Run time per sample", "label")
            self._image = ui.image().classes("w-full rounded-lg")
        self._card.set_visibility(False)   # hidden until there is something to show

    def show(self, plot_path: Path) -> None:
        url = app.add_static_file(local_file=plot_path)
        self._image.set_source(url)
        self._card.set_visibility(True)

    def hide(self) -> None:
        self._card.set_visibility(False)