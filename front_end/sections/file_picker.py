from typing import Callable, Optional
from nicegui import ui
from back_end.ui_assisting_files.file_pairing import INPUT_DIR, PRIMER_SUFFIXES, find_pairs
from front_end.components.button_comp import button
from front_end.components.text_comp import text

class FilePicker:
    """
        This section searches for pairs of files based on chosen primer. 
        It finds files with the same sample name and with the correct forward and reverse
        primer names to create a pair. It creates a list of selectable pairs that can be chosen
        to proceed in the pipeline with. It also makes a list of unpaired files found and additional
        input files that don't match the primer type.
    """
    def __init__(
        self,
        log: Callable[[str], None],
        on_change: Optional[Callable[[], None]] = None,
    ) -> None:
        self._log = log
        self._on_change = on_change

        self._primer: Optional[int] = None        
        self._scanned_primer: Optional[int] = None
        self._checkboxes: dict[str, ui.checkbox] = {}
        self._select_all: Optional[ui.checkbox] = None
        self._count_label: Optional[ui.label] = None
        self._updating = False
        self._build()

    # UI
    def _build(self) -> None:
        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-4"):
            text("Input files", "label")
            text(
                "Choose a primer above, then search the input folder for sample pairs.",
                "description",
            )
            self._find_button = button(
                "Find sample pairs", self._find_files, variant="secondary", icon="search"
            )
            self._find_button.set_enabled(False)
            self._results = ui.column().classes("w-full gap-3")
        self._results.set_visibility(False)

    def _find_files(self) -> None:
        """
            Compile lists of pairs, unpaired and unrecognised files.
        """
        try:
            result = find_pairs(self._primer)
        except FileNotFoundError:
            self._log(f"Input folder not found: {INPUT_DIR}")
            ui.notify("Input folder not found", type="negative")
            return

        self._clear_results()
        self._scanned_primer = self._primer

        # Compile lists
        with self._results:
            if result.samples:
                self._build_sample_list(result.samples)
            else:
                text("No complete sample pairs were found.", "body")
            if result.unpaired:
                self._build_unpaired(result.unpaired)
            if result.unrecognised:
                self._build_unrecognised(result.unrecognised)
        self._results.set_visibility(True)

        # Report amount of files found.
        self._log(
            f"Found {len(result.samples)} complete pair(s), "
            f"{len(result.unpaired)} unpaired file(s)"
        )
        self._notify()

    def _build_sample_list(self, samples: list[str]) -> None:
        """
            Makes checkbox that can either select all samples or only specific ones. This
            makes the list of samples that will be used in the pipeline.
        """
        # Select all checkbox
        with ui.row().classes("w-full justify-between items-center"):
            self._select_all = ui.checkbox("Select all", on_change=self._handle_select_all)
            self._count_label = text("", "description")

        # Sample specific checkboxes
        with ui.scroll_area().classes("w-full h-48 border rounded-lg px-3"):
            for sample in samples:
                self._checkboxes[sample] = ui.checkbox(
                    sample, on_change=self._handle_sample_change
                )
        self._update_count()

    def _build_unpaired(self, unpaired) -> None:
        """
            Builds the list of unpaired file names. 
        """
        with ui.column().classes("w-full gap-1 rounded-lg bg-amber-50 p-3"):
            text("Files missing their pair (these will be skipped)", "label")
            for item in unpaired:
                with ui.row().classes("items-center gap-2"):
                    ui.icon("warning", color="warning")
                    text(f"{item.file_name}  (no {item.missing} file found)", "body")

    def _build_unrecognised(self, file_names: list[str]) -> None:
        """
            Builds list of unrecognised input files. Files are classified as unrecognised
            if it is not for the primer specified.
        """
        with ui.column().classes("w-full gap-1 rounded-lg bg-slate-100 p-3"):
            text("Files not recognised for this primer (ignored)", "label")
            for name in file_names:
                text(name, "body")

    # Event handlers
    def _handle_select_all(self, e) -> None:
        """
            When select all checkbox has been selected, all the sample checkboxes are also ticked. 
            Those files get added to the list of selected samples.
        """
        if self._updating:
            return
        self._updating = True
        for checkbox in self._checkboxes.values():
            checkbox.value = e.value
        self._updating = False
        self._update_count()
        self._notify()

    def _handle_sample_change(self) -> None:
        """
            This updates the selected samples list when a sample's checkbox is clicked or unclicked.
        """
        if self._updating:
            return
        self._updating = True
        self._select_all.value = len(self.selected_samples()) == len(self._checkboxes)
        self._updating = False
        self._update_count()
        self._notify()

    def _update_count(self) -> None:
        """
            This updates the counter of how many samples have been selected for the pipeline.
        """
        if self._count_label:
            self._count_label.set_text(
                f"{len(self.selected_samples())} of {len(self._checkboxes)} selected"
            )

    def _notify(self) -> None:
        if self._on_change:
            self._on_change()

    def _clear_results(self) -> None:
        """
            Clear all checkboxes, counters and the primer used for file searching. Also clears 
            and closes result panel.
        """
        self._results.clear()
        self._results.set_visibility(False)
        self._checkboxes.clear()
        self._select_all = None
        self._count_label = None
        self._scanned_primer = None

    # The home page requires these methods
    def rescan(self) -> None:
        """
            Search again after new files arrived. Does nothing if no search has
            been done yet, and keeps the samples the user already ticked.
        """
        if self._scanned_primer is None:
            return
        # Keeps previously selected samples
        previously_selected = set(self.selected_samples())
        self._find_files()
        for name in previously_selected:
            if name in self._checkboxes:
                self._checkboxes[name].value = True
    
    def update_primer(self, primer: Optional[int]) -> None:
        """
            Call whenever the primer settings change. The list built for another primer
            is thrown away.
        """
        self._primer = primer
        self._find_button.set_enabled(primer is not None)
        if self._scanned_primer is not None and primer != self._scanned_primer:
            self._clear_results()

    def selected_samples(self) -> list[str]:
        """"
            Returns the list of selected samples by finding all the samples with ticked checkboxes.
        """
        return [name for name, box in self._checkboxes.items() if box.value]

    @property
    def has_selection(self) -> bool:
        return any(box.value for box in self._checkboxes.values())

    def set_enabled(self, enabled: bool) -> None:
        """
            Lock or unlock the whole section (used while the pipeline runs).
        """
        self._find_button.set_enabled(enabled and self._primer is not None)
        if self._select_all:
            self._select_all.set_enabled(enabled)
        for box in self._checkboxes.values():
            box.set_enabled(enabled)