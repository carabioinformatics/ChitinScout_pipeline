"""Sample status table: one row per sample, one column per pipeline step."""
from nicegui import ui
from typing import Callable, Optional
from pathlib import Path
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
RESULTS_READY_STEP = "summary"

class SampleStatusTable:
    """Shows a status icon for every sample/step. Click a red cross for the error."""

    def __init__(
        self,
        on_view_results: Callable[[str], None],
        on_close_results: Callable[[], None],
    ) -> None:
        self._on_view_results = on_view_results
        self._on_close_results = on_close_results

        self._cells: dict[tuple[str, str], ui.button] = {}
        self._status: dict[tuple[str, str], str] = {}
        self._errors: dict[tuple[str, str], str] = {}
        self._results_buttons: dict[str, ui.button] = {}
        self._open_sample: Optional[str] = None
        self._samples: list[str] = []
        self._build()

    # ---- UI
    def _build(self) -> None:
        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-3") as self._card:
            text("Sample progress", "label")
            with ui.element("div").classes("w-full max-h-72 overflow-auto"):
                self._grid = ui.grid(
                    columns=f"9rem repeat({len(STEPS)}, 6rem) 7rem"
                ).classes("min-w-max gap-x-2 gap-y-1 items-center")
            text("Click a red cross to see why a step failed.", "description")
        self._card.set_visibility(False)        
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

    def _toggle_results(self, sample: str) -> None:
        if self._open_sample == sample:
            self._close_results()
            return
        if self._open_sample is not None:           # another sample was open
            self._set_button_state(self._open_sample, is_open=False)
        self._open_sample = sample
        self._set_button_state(sample, is_open=True)
        self._on_view_results(sample)

    def _close_results(self) -> None:
        if self._open_sample is not None:
            self._set_button_state(self._open_sample, is_open=False)
        self._open_sample = None
        self._on_close_results()

    def _set_button_state(self, sample: str, is_open: bool) -> None:
        results_button = self._results_buttons.get(sample)
        if results_button is None:
            return
        results_button.set_text("Close" if is_open else "View")
        results_button.props(f"icon={'close' if is_open else 'visibility'}")

    # ---- What the page needs from this section
    def reset(self, samples: list[str]) -> None:
        """Start a fresh table: every step of every sample is waiting."""
        self._samples = list(samples)
        self._cells.clear()
        self._status.clear()
        self._errors.clear()
        self._results_buttons.clear()
        self._open_sample = None
        self._on_close_results()         
        self._grid.clear()

        with self._grid:
            text("Sample", "label")
            for _, label in STEPS:
                text(label, "label").classes("text-center")
            text("Results", "label").classes("text-center")
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

                results_button = (
                    ui.button("View", icon="visibility",
                              on_click=lambda s=sample: self._toggle_results(s))
                    .props("flat dense no-caps color=primary")
                    .classes("justify-self-center")
                )
                results_button.set_enabled(False)   # unlocked when the summary is done
                self._results_buttons[sample] = results_button
        self._card.set_visibility(bool(samples))

    def set_step(self, sample: str, step: str, status: str, message: str = "") -> None:
        key = (sample, step)
        if key not in self._cells or status not in CELL_STYLE:
            return
        self._status[key] = status
        if status == "done" and step == RESULTS_READY_STEP:
            self._results_buttons[sample].set_enabled(True)        
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