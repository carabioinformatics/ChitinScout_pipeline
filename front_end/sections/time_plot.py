from pathlib import Path
from nicegui import app, ui
from front_end.components.text_comp import text

class TimePlot:
    """
        Timeplot section shows the already created graph of all the samples that went through the pipeline and the 
        time each took. This is only visible once the whole pipeline is complete.
    """
    def __init__(self) -> None:
        self._card = ui.card().classes("w-full rounded-xl shadow-md p-6 gap-3")
        with self._card:
            text("Run time per sample", "label")
            self._image = ui.image().classes("w-full rounded-lg")
        self._card.set_visibility(False)

    def show(self, plot_path: Path) -> None:
        url = app.add_static_file(local_file=plot_path)
        self._image.set_source(url)
        self._card.set_visibility(True)

    def hide(self) -> None:
        self._card.set_visibility(False)