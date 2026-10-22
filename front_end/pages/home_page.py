"""The home page: welcome, primer choice, run button, status."""
import asyncio

from nicegui import ui

from front_end.components.button_comp import button
from front_end.components.dropdown_comp import dropdown
from front_end.components.text_comp import text
from front_end.theme import apply_theme

# --- Pipeline options -------------------------------------------------
# key -> label shown in the dropdown. Later you can also map each key
# to its back-end script, e.g. {"its": its_pipeline.run, "tef": tef_pipeline.run}
PIPELINES = {
    "its": "ITS primer pipeline",
    "tef": "TEF primer pipeline",
}

# --- Status states ----------------------------------------------------
# state -> (message, Quasar colour, icon)
STATUS = {
    "waiting":   ("Waiting for primer choice", "grey",     "hourglass_empty"),
    "starting":  ("Starting with run",         "info",     "play_circle"),
    "busy":      ("Busy with pipeline",        "warning",  "autorenew"),
    "completed": ("Pipeline completed",        "positive", "check_circle"),
}


def home_page() -> None:
    apply_theme()

    # State for this window/session
    state = {"status": "waiting", "primer": None}

    # @ui.refreshable lets us redraw the status chip when the state changes
    @ui.refreshable
    def status_display() -> None:
        message, color, icon = STATUS[state["status"]]
        ui.chip(message, icon=icon, color=color, text_color="white").props("size=lg")

    def set_status(new_status: str) -> None:
        state["status"] = new_status
        status_display.refresh()

    # ---- Event handlers
    def on_primer_change(e) -> None:
        state["primer"] = e.value
        run_button.set_enabled(e.value is not None)
        set_status("waiting")

    async def on_run_click() -> None:
        run_button.set_enabled(False)
        primer_select.set_enabled(False)

        set_status("starting")
        await asyncio.sleep(1)

        set_status("busy")
        # PLACEHOLDER: this is where the back-end gets called later, e.g.
        #   from nicegui import run
        #   await run.cpu_bound(its_pipeline.run, ...)
        await asyncio.sleep(3)

        set_status("completed")
        run_button.set_enabled(True)
        primer_select.set_enabled(True)

    # ---- Layout
    with ui.column().classes("w-full max-w-3xl mx-auto gap-6 p-8"):

        with ui.column().classes("gap-1"):
            text("Welcome", "title")
            text(
                "Choose a primer set below and start the sequencing pipeline.",
                "description",
            )

        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-4"):
            text("Pipeline settings", "label")
            primer_select = dropdown(
                label="Primer choice",
                options=PIPELINES,
                on_change=on_primer_change,
            )
            run_button = button("Run pipeline", on_run_click, icon="play_arrow")
            run_button.set_enabled(False)

        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-3"):
            text("Status", "label")
            status_display()