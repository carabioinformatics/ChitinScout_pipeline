"""Sample status table: one row per sample, one column per pipeline step."""
from nicegui import ui

from back_end.pipeline_steps import STEPS
from front_end.components.button_comp import button
from front_end.components.text_comp import text

# status -> (icon, Quasar colour)
CELL_STYLE = {
    "waiting": ("pause_circle", "grey-6"),
    "running": ("autorenew", "warning"),
    "done":    ("check_circle", "positive"),
    "failed":  ("cancel", "negative"),
}
STEP_LABELS = dict(STEPS)


class SampleStatusTable:
    """Shows a status icon for every sample/step. Click a red cross for the error."""

    def __init__(self) -> None:
        self._cells: dict[tuple[str, str], ui.button] = {}
        self._status: dict[tuple[str, str], str] = {}
        self._errors: dict[tuple[str, str], str] = {}
        self._samples: list[str] = []
        self._build()

    # ---- UI
    def _build(self) -> None:
        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-3") as self._card:
            text("Sample progress", "label")
            with ui.scroll_area().classes("w-full h-72"):
                self._grid = ui.grid(
                    columns=f"8rem repeat({len(STEPS)}, minmax(5rem, 1fr))"
                ).classes("w-full gap-x-2 gap-y-1 items-center")
            text("Click a red cross to see why a step failed.", "description")
        self._card.set_visibility(False)   # hidden until a run starts

        # One shared error dialog, filled in when a red cross is clicked
        with ui.dialog() as self._dialog, ui.card().classes("p-6 gap-3 w-96"):
            self._dialog_title = text("", "body").classes("font-semibold")
            self._dialog_message = text("", "body").classes("whitespace-pre-wrap")
            with ui.row().classes("w-full justify-end"):
                button("Close", self._dialog.close, variant="secondary")

    def _apply(self, key: tuple[str, str]) -> None:
        status = self._status[key]
        icon, color = CELL_STYLE[status]
        cell = self._cells[key]
        cell.props(f"icon={icon} color={color}")
        if status == "running":
            cell.classes(add="animate-spin")
        else:
            cell.classes(remove="animate-spin")

    def _show_error(self, sample: str, step: str) -> None:
        key = (sample, step)
        if self._status.get(key) != "failed":
            return
        self._dialog_title.set_text(f"{sample}: {STEP_LABELS[step]} failed")
        self._dialog_message.set_text(self._errors.get(key, ""))
        self._dialog.open()

    # ---- What the page needs from this section
    def reset(self, samples: list[str]) -> None:
        """Start a fresh table: every step of every sample is waiting."""
        self._samples = list(samples)
        self._cells.clear()
        self._status.clear()
        self._errors.clear()
        self._grid.clear()

        with self._grid:
            text("Sample", "label")
            for _, label in STEPS:
                text(label, "label").classes("text-center")
            for sample in samples:
                text(sample, "body").classes("truncate")
                for step_id, _ in STEPS:
                    key = (sample, step_id)
                    self._cells[key] = (
                        ui.button(on_click=lambda s=sample, st=step_id: self._show_error(s, st))
                        .props("flat round dense")
                        .classes("justify-self-center")
                    )
                    self._status[key] = "waiting"
                    self._apply(key)

        self._card.set_visibility(bool(samples))

    def set_step(self, sample: str, step: str, status: str, message: str = "") -> None:
        key = (sample, step)
        if key not in self._cells or status not in CELL_STYLE:
            return
        self._status[key] = status
        if status == "failed":
            self._errors[key] = message or "No error message was reported."
        self._apply(key)

    def fail_current(self, sample: str, message: str) -> None:
        """Mark the step this sample was busy with as failed.

        If a step already reported its own failure, nothing is changed. If no step
        had started yet (e.g. a missing file), the first step is marked."""
        steps = [step_id for step_id, _ in STEPS if (sample, step_id) in self._cells]
        if not steps:
            return
        if any(self._status[(sample, s)] == "failed" for s in steps):
            return
        target = next(
            (s for s in steps if self._status[(sample, s)] == "running"),
            next((s for s in steps if self._status[(sample, s)] == "waiting"), None),
        )
        if target:
            self.set_step(sample, target, "failed", message)

    def halt(self) -> None:
        """Call when a run ends: steps still 'in progress' go back to waiting
        (they were interrupted), so no spinner is left turning."""
        for key, status in self._status.items():
            if status == "running":
                self._status[key] = "waiting"
                self._apply(key)