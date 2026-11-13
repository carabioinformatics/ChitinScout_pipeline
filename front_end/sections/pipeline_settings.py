from typing import Callable, Optional
from nicegui import ui
from front_end.components.dropdown_comp import dropdown
from front_end.components.text_comp import text
from back_end.ui_assisting_files.primer_store import primer_labels, add_primer

# List types of pipeline mode options, more can be added here
TAXONOMY_MODES = {
    0: "Just a BLAST search and summary",
    1: "BLAST search, counter of each species and summary",
}
DATABASE_MODES = {
    0: "BLAST search using NCBI and UNITE database",
    1: "BLAST search using only NCBI database",
    2: "BLAST search using only UNITE database",
}

class PipelineSettings:
    """
        This section collects all the pipeline setting related data. This includes which primer
        is used, what taxonomy mode to use, and which databases to reference with BLAST. This 
        is done using dropdown boxes and saves changes.
    """
    def __init__(
        self,
        log: Callable[[str], None],
        on_change: Optional[Callable[[], None]] = None,
    ) -> None:
        self._log = log
        self._on_change = on_change
        self.primer: Optional[int] = None
        self.taxonomy_mode: int = next(iter(TAXONOMY_MODES))
        self.database_mode: int = next(iter(DATABASE_MODES))

        self._build()

    # ---- UI
    def _build(self) -> None:
        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-4"):
            text("Pipeline settings", "label")
            # Primer dropdown
            self._primer_select = dropdown(
                "Primer choice", primer_labels(), on_change=self._handle_primer
            )      

            # Add-a-primer form
            self._add_expansion = ui.expansion("Add a new primer", icon="add").classes("w-full")
            with self._add_expansion:
                self._fwd_name = ui.input("Forward primer name").classes("w-full")
                self._rev_name = ui.input("Reverse primer name").classes("w-full")
                self._fwd_suffix = ui.input(
                    "Forward file suffix", placeholder="e.g. ITS1___1.ab1"
                ).classes("w-full")
                self._rev_suffix = ui.input(
                    "Reverse file suffix", placeholder="e.g. ITS4___1.ab1"
                ).classes("w-full")
                self._save_button = ui.button("Save primer", on_click=self._handle_add_primer)            # Taxonomy mode dropdown
            self._taxonomy_select = dropdown(
                "Taxonomy mode", TAXONOMY_MODES,
                value=self.taxonomy_mode, on_change=self._handle_taxonomy,
            )
            # Database mode dropdown
            self._database_select = dropdown(
                "Database mode", DATABASE_MODES,
                value=self.database_mode, on_change=self._handle_database,
            )

    # Event handlers
    def _handle_primer(self, e) -> None:
            """
                Selects and logs which primer has been selected from the primer dropdown.
            """
            self.primer = e.value
            if e.value is not None:
                self._log(f"Primer selected: {primer_labels()[e.value]}")
            self._notify()
    
    def _handle_add_primer(self) -> None:
        """
            Validates and saves a new primer to primers.json, then adds it to the
            dropdown and selects it.
        """
        try:
            new_index = add_primer(
                self._fwd_name.value or "",
                self._rev_name.value or "",
                self._fwd_suffix.value or "",
                self._rev_suffix.value or "",
            )
        except ValueError as err:
            ui.notify(str(err), type="warning")
            return
        except OSError as err:
            ui.notify(f"Could not save primer: {err}", type="negative")
            return

        # Refresh the dropdown and select the new primer (this fires _handle_primer)
        self._primer_select.set_options(primer_labels(), value=new_index)
        self._log(f"New primer saved: {primer_labels()[new_index]}")
        ui.notify("Primer saved", type="positive")

        for field in (self._fwd_name, self._rev_name, self._fwd_suffix, self._rev_suffix):
            field.set_value("")
        self._add_expansion.close()

    def _handle_taxonomy(self, e) -> None:
        """"
            Selects and logs which mode has been selected from the taxonomy dropdown.
        """
        self.taxonomy_mode = e.value
        self._log(f"Taxonomy mode selected: {TAXONOMY_MODES[e.value]}")
        self._notify()

    def _handle_database(self, e) -> None:
        """
            Selects and logs which mode has been selected from database dropdown.
        """
        self.database_mode = e.value
        self._log(f"Database mode selected: {DATABASE_MODES[e.value]}")
        self._notify()

    def _notify(self) -> None:
        if self._on_change:
            self._on_change()

    # Values used by other pages
    @property
    def is_complete(self) -> bool:
        """
            True once the user has made every required choice.
        """
        return self.primer is not None

    def extra_args(self) -> list[str]:
        """
            Arguments that follow the primer mode: run.sh <primer> <taxonomy> <database>
        """
        return [str(self.taxonomy_mode), str(self.database_mode)]

    def set_enabled(self, enabled: bool) -> None:
        """
            Lock or unlock all dropdowns (used while the pipeline runs).
        """
        for control in (
            self._primer_select, self._taxonomy_select, self._database_select,
            self._fwd_name, self._rev_name, self._fwd_suffix, self._rev_suffix,
            self._save_button,
        ):
            control.set_enabled(enabled)