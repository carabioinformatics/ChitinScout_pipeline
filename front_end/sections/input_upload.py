from collections import Counter
from typing import Callable, Optional
from nicegui import ui
from back_end.ui_assisting_files.input_file_add import Outcome, count_input_files, store_input_file
from front_end.components.text_comp import text

MAX_FILE_SIZE = 20 * 1024 * 1024   # 20 MB per file; .ab1 files are normally far smaller

async def _read_upload(e) -> tuple[str, bytes]:
    """
        Get the file name and content from an upload event.
    """
    if hasattr(e, "file"):
        return e.file.name, await e.file.read()
    return e.name, e.content.read()

class InputUpload:
    """
        This section creates an environment to upload documents (only .ab1 is allowed) that can be saved to the input
        folder. This also includes a file counter. The sample list is also updated once more 
        files have been added.
    """
    def __init__(
        self,
        log: Callable[[str], None],
        on_files_added: Optional[Callable[[], None]] = None,
    ) -> None:
        self._log = log
        self._on_files_added = on_files_added
        self._batch: list[Outcome] = []

        self._build()
        self._update_folder_count()

    # UI components
    def _build(self) -> None:
        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-3"):
            text("Add input files", "label")
            text(
                "Drag your .ab1 files here, or click + to browse. "
                "They are copied into the project's Input folder for you.",
                "description",
            )
            self._upload = (
                ui.upload(
                    label="Drop .ab1 files here",
                    multiple=True,
                    auto_upload=True,
                    max_file_size=MAX_FILE_SIZE,
                    on_upload=self._handle_upload,
                    on_multi_upload=self._handle_batch_done,
                    on_rejected=self._handle_rejected,
                )
                .props('accept=".ab1" flat bordered')
                .classes("w-full")
            )
            self._summary = text("", "body")
            self._folder_count = text("", "description")

    # Event handlers
    async def _handle_upload(self, e) -> None:
        """
            Runs once for every file that arrives and allows file to be uploaded.
        """
        file_name, content = await _read_upload(e)
        outcome, message = store_input_file(file_name, content)
        self._batch.append(outcome)
        self._log(message)

    def _handle_batch_done(self, e=None) -> None:
        """
            Runs once after all files of one drop/selection have arrived and uploads file to the input folder.
        """
        counts = Counter(self._batch)
        self._batch = []

        # Report which files were added or not
        parts = []
        if counts[Outcome.ADDED]:
            parts.append(f"added {counts[Outcome.ADDED]}")
        if counts[Outcome.REPLACED]:
            parts.append(f"replaced {counts[Outcome.REPLACED]}")
        if counts[Outcome.REJECTED]:
            parts.append(f"skipped {counts[Outcome.REJECTED]} (not .ab1 or empty)")
        summary = "Upload finished: " + ", ".join(parts) if parts else ""
        self._summary.set_text(summary)

        self._upload.reset()
        # Get new count of input files
        self._update_folder_count()
        if (counts[Outcome.ADDED] or counts[Outcome.REPLACED]) and self._on_files_added:
            self._on_files_added()

    def _handle_rejected(self, e=None) -> None:
        """
            Runs when the browser itself refuses a file (wrong type or too large).
        """
        ui.notify("Some files were rejected: only .ab1 files up to 20 MB are accepted",
                  type="warning")

    def _update_folder_count(self) -> None:
        """
            Updates the total count of files in the Input folder.
        """
        self._folder_count.set_text(
            f"The Input folder currently holds {count_input_files()} .ab1 file(s)."
        )

    # This is what is passed to the next page
    def set_enabled(self, enabled: bool) -> None:
        """
            Lock or unlock the uploader (used while the pipeline runs).
        """
        self._upload.set_enabled(enabled)