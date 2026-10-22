"""The home page: welcome, settings sections, run button, status, live output."""
import asyncio

from nicegui import app, ui
from back_end.runner import PipelineRunner
from front_end.components.button_comp import button
from front_end.components.text_comp import text
from front_end.sections.pipeline_settings import PipelineSettings
from front_end.sections.search_thresholds import SearchThresholds
from front_end.theme import apply_theme

# --- Status states ----------------------------------------------------
# state -> (message, Quasar colour, icon)
STATUS = {
    "waiting":   ("Waiting for pipeline parameters", "grey",     "hourglass_empty"),
    "starting":  ("Starting with run",         "info",     "play_circle"),
    "busy":      ("Busy with pipeline",        "warning",  "autorenew"),
    "completed": ("Pipeline completed",        "positive", "check_circle"),
    "failed":    ("Pipeline failed",           "negative", "error"),
    "stopped":   ("Pipeline stopped",          "blue-grey", "stop_circle"),
}


def home_page() -> None:
    apply_theme()

    state = {"status": "waiting"}
    runner = PipelineRunner()

    @ui.refreshable
    def status_display() -> None:
        message, color, icon = STATUS[state["status"]]
        ui.chip(message, icon=icon, color=color, text_color="white").props("size=lg")

    def set_status(new_status: str) -> None:
        state["status"] = new_status
        status_display.refresh()

    def log(message: str) -> None:
        """Passed to every section so they can all write to the output log.
        output_log is created further down; this is only called later."""
        output_log.push(message)

    # ---- Event handlers
    def on_settings_change() -> None:
        run_button.set_enabled(settings.is_complete)
        set_status("waiting")

    def set_inputs_enabled(enabled: bool) -> None:
        settings.set_enabled(enabled)
        thresholds.set_enabled(enabled)
        run_button.set_enabled(enabled and settings.is_complete)
        stop_button.set_enabled(not enabled)

    async def on_run_click() -> None:
        set_inputs_enabled(False)
        output_log.clear()
        set_status("starting")

        # search_thresholds = thresholds.values()
        log(thresholds.describe())
        # log(f"Search thresholds: {search_thresholds}")

        try:
            exit_code = await runner.run(
                primer_mode=settings.primer,
                extra_args=settings.extra_args() + thresholds.extra_args(),
                on_start=lambda: set_status("busy"),
                on_output=log,
            )
            if runner.was_stopped:
                log("Pipeline stopped by user. Click Run to start again.")
                set_status("stopped")
            else: 
                set_status("completed" if exit_code == 0 else "failed")
        except Exception as error:   # e.g. bash not found, script missing
            log(f"Could not start pipeline: {error}")
            set_status("failed")
        finally:
            set_inputs_enabled(True)

    async def on_stop_click() -> None:
        stop_button.set_enabled(False)
        log("Stopping pipeline...")
        await runner.stop()

    async def on_quit_confirmed() -> None:
        confirm_dialog.close()
        await runner.stop()              # never leave the pipeline running in the background
        goodbye_dialog.open()
        ui.run_javascript("window.close()")   # browsers often block this; the message covers that
        await asyncio.sleep(0.5)         # let the message reach the browser
        app.shutdown()

    # ---- Layout
    with ui.column().classes("w-full max-w-3xl mx-auto gap-6 p-8"):

        with ui.column().classes("gap-1"):
            text("Welcome", "title")
            text(
                "Choose your settings below and start the sequencing pipeline.",
                "description",
            )

        settings = PipelineSettings(log=log, on_change=on_settings_change)
        thresholds = SearchThresholds(log=log)

        run_button = button("Run pipeline", on_run_click, icon="play_arrow")
        run_button.set_enabled(False)

        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-3"):
            text("Status", "label")
            status_display()

        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-3"):
            text("Pipeline output", "label")
            output_log = ui.log(max_lines=500).classes("w-full h-64")

        # ---- Bottom buttons
        with ui.row().classes("w-full justify-between"):
            stop_button = button(
                "Stop pipeline", on_stop_click, variant="danger", icon="stop"
            )
            stop_button.set_enabled(False)

            quit_button = button(
                "Quit application", lambda: confirm_dialog.open(),
                variant="secondary", icon="power_settings_new",
            )

    # ---- Dialogs (hidden until opened)
    with ui.dialog() as confirm_dialog, ui.card().classes("p-6 gap-4"):
        text("Quit the application?", "body")
        text("Any running pipeline will be stopped.", "description")
        with ui.row().classes("w-full justify-end"):
            button("Cancel", confirm_dialog.close, variant="secondary")
            button("Quit", on_quit_confirmed, variant="danger")

    with ui.dialog().props("persistent") as goodbye_dialog, ui.card().classes("p-6 gap-2"):
        text("Application stopped", "body").classes("font-semibold")
        text("You can now close this tab.", "description")