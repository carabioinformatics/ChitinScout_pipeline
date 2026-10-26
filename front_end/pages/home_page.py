"""The home page: welcome, settings sections, run button, status, live output."""
import asyncio

from nicegui import app, ui
from back_end.runner import PipelineRunner
from front_end.components.button_comp import button
from front_end.components.text_comp import text
from front_end.components.progress_bar_comp import SampleProgress
from front_end.sections.pipeline_settings import PipelineSettings
from front_end.sections.search_thresholds import SearchThresholds
from front_end.sections.file_picker import FilePicker
from front_end.sections.time_plot import TimePlot
from front_end.sections.input_upload import InputUpload
from front_end.theme import apply_theme

# --- Status states ----------------------------------------------------
# state -> (message, Quasar colour, icon)
STATUS = {
    "waiting":        ("Waiting for primer choice",     "grey",      "hourglass_empty"),
    "select_samples": ("Waiting for sample selection",  "grey",      "checklist"),
    "ready":          ("Ready to run",                  "primary",   "task_alt"),
    "starting":       ("Starting with run",             "info",      "play_circle"),
    "busy":           ("Busy with pipeline",            "warning",   "autorenew"),
    "completed":      ("Pipeline completed",            "positive",  "check_circle"),
    "failed":         ("Pipeline failed",               "negative",  "error"),
    "stopped":        ("Pipeline stopped",              "blue-grey", "stop_circle"),
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
    def update_ready_state() -> None:
        """Decide whether Run can be clicked and what the status should say."""
        ready = settings.is_complete and file_picker.has_selection
        run_button.set_enabled(ready)

        if not settings.is_complete:
            set_status("waiting")
        elif not file_picker.has_selection:
            set_status("select_samples")
        else:
            set_status("ready")

        # Shows "0 of N samples complete" for the current selection
        progress.update(0, len(file_picker.selected_samples()))

    def on_settings_change() -> None:
        file_picker.update_primer(settings.primer)   # may discard a stale list
        update_ready_state()

    def set_inputs_enabled(enabled: bool) -> None:
        settings.set_enabled(enabled)
        thresholds.set_enabled(enabled)
        input_upload.set_enabled(enabled)
        file_picker.set_enabled(enabled)
        run_button.set_enabled(
            enabled and settings.is_complete and file_picker.has_selection
        )        
        stop_button.set_enabled(not enabled)

    async def on_run_click() -> None:
        samples = file_picker.selected_samples()

        set_inputs_enabled(False)
        output_log.clear()
        time_plot.hide()
        set_status("starting")
        progress.update(0, len(samples))

        log(f"Samples selected: {', '.join(samples)}")
        log(thresholds.describe())
        plot_path = None

        def on_plot(path) -> None:
            nonlocal plot_path
            plot_path = path

        try:
            exit_code = await runner.run(
                primer_mode=settings.primer,
                extra_args=settings.extra_args() + thresholds.extra_args(),
                sample_names=samples,
                on_start=lambda: set_status("busy"),
                on_output=log,
                on_progress=progress.update,
                on_plot=on_plot,
            )
            if runner.was_stopped:
                log("Pipeline stopped by user. Click Run to start again.")
                set_status("stopped")
            else: 
                set_status("completed" if exit_code == 0 else "failed")
                if exit_code == 0 and plot_path and plot_path.is_file():
                    time_plot.show(plot_path)        
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
            text("Welcome to ChitinScout", "title")
            text(
                "Choose your settings below and start the sequencing pipeline.",
                "description",
            )

        settings = PipelineSettings(log=log, on_change=on_settings_change)
        thresholds = SearchThresholds(log=log)
        input_upload = InputUpload(log=log, on_files_added=lambda: file_picker.rescan())        
        file_picker = FilePicker(log=log, on_change=update_ready_state)

        run_button = button("Run pipeline", on_run_click, icon="play_arrow")
        run_button.set_enabled(False)

        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-3"):
            text("Status", "label")
            status_display()
            progress = SampleProgress()

        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-3"):
            text("Pipeline output", "label")
            output_log = ui.log(max_lines=500).classes("w-full h-64")

        time_plot = TimePlot()

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