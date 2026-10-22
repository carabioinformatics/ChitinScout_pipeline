"""Reusable progress bar showing 'X of Y samples complete' and a percentage."""
from nicegui import ui
from front_end.components.text_comp import text


class SampleProgress:
    def __init__(self) -> None:
        with ui.column().classes("w-full gap-1"):
            with ui.row().classes("w-full justify-between items-center"):
                self._count_label = text("", "body")
                self._percent_label = text("", "body").classes("font-semibold")
            self._bar = ui.linear_progress(value=0, show_value=False).props(
                "rounded size=12px"
            )
        self.update(0, 0)

    def update(self, done: int, total: int) -> None:
        if total == 0:
            self._bar.value = 0
            self._count_label.set_text("No samples selected")
            self._percent_label.set_text("")
            return

        fraction = done / total
        self._bar.value = fraction
        self._count_label.set_text(f"{done} of {total} samples complete")
        self._percent_label.set_text(f"{round(fraction * 100)}%")