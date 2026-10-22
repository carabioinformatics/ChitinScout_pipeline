"""The home page: welcome, primer choice, run button, status, live output."""
from nicegui import ui

from back_end.runner import run_pipeline
from front_end.components.button_comp import button
from front_end.components.dropdown_comp import dropdown
from front_end.components.text_comp import text
from front_end.theme import apply_theme

# --- Pipeline options -------------------------------------------------
# value passed to run.sh -> label shown in the dropdown
PIPELINES = {
    0: "ITS primer pipeline",
    1: "TEF primer pipeline",
}

# --- Status states ----------------------------------------------------
# state -> (message, Quasar colour, icon)
STATUS = {
    "waiting":   ("Waiting for primer choice", "grey",     "hourglass_empty"),
    "starting":  ("Starting with run",         "info",     "play_circle"),
    "busy":      ("Busy with pipeline",        "warning",  "autorenew"),
    "completed": ("Pipeline completed",        "positive", "check_circle"),
    "failed":    ("Pipeline failed",           "negative", "error"),
}


def home_page() -> None:
    apply_theme()

    state = {"status": "waiting", "primer": None}

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
        # "is not None" matters: the ITS value is 0, which is falsy in Python
        run_button.set_enabled(e.value is not None)
        set_status("waiting")

    async def on_run_click() -> None:
        run_button.set_enabled(False)
        primer_select.set_enabled(False)
        output_log.clear()
        set_status("starting")

        try:
            exit_code = await run_pipeline(
                primer_mode=state["primer"],
                on_start=lambda: set_status("busy"),
                on_output=output_log.push,
            )
            set_status("completed" if exit_code == 0 else "failed")
        except Exception as error:   # e.g. bash not found, script missing
            output_log.push(f"Could not start pipeline: {error}")
            set_status("failed")
        finally:
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

        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-3"):
            text("Pipeline output", "label")
            output_log = ui.log(max_lines=500).classes("w-full h-64")