"""Pipeline settings section: primer, taxonomy mode and database mode."""
from typing import Callable, Optional

from nicegui import ui
from front_end.components.dropdown_comp import dropdown
from front_end.components.text_comp import text

# value passed to run.sh -> label shown to the user.
# Replace the taxonomy/database labels with the real names of your modes.
PRIMERS = {
    0: "ITS1 + ITS4 primers",
    1: "TEF forward and reverse primers",
}
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
    """Owns the three dropdowns and everything about them.

    log:       function that prints a line to the output log
    on_change: called whenever any dropdown changes (the page uses this
               to enable/disable the run button)
    """

    def __init__(
        self,
        log: Callable[[str], None],
        on_change: Optional[Callable[[], None]] = None,
    ) -> None:
        self._log = log
        self._on_change = on_change

        # The primer has no default; the user must choose it.
        # The other two start on their first option.
        self.primer: Optional[int] = None
        self.taxonomy_mode: int = next(iter(TAXONOMY_MODES))
        self.database_mode: int = next(iter(DATABASE_MODES))

        self._build()

    # ---- UI
    def _build(self) -> None:
        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-4"):
            text("Pipeline settings", "label")
            self._primer_select = dropdown(
                "Primer choice", PRIMERS, on_change=self._handle_primer
            )
            self._taxonomy_select = dropdown(
                "Taxonomy mode", TAXONOMY_MODES,
                value=self.taxonomy_mode, on_change=self._handle_taxonomy,
            )
            self._database_select = dropdown(
                "Database mode", DATABASE_MODES,
                value=self.database_mode, on_change=self._handle_database,
            )

    # ---- Event handlers
    def _handle_primer(self, e) -> None:
        self.primer = e.value
        if e.value is not None:
            self._log(f"Primer selected: {PRIMERS[e.value]}")
        self._notify()

    def _handle_taxonomy(self, e) -> None:
        self.taxonomy_mode = e.value
        self._log(f"Taxonomy mode selected: {TAXONOMY_MODES[e.value]}")
        self._notify()

    def _handle_database(self, e) -> None:
        self.database_mode = e.value
        self._log(f"Database mode selected: {DATABASE_MODES[e.value]}")
        self._notify()

    def _notify(self) -> None:
        if self._on_change:
            self._on_change()

    # ---- What the page needs from this section
    @property
    def is_complete(self) -> bool:
        """True once the user has made every required choice."""
        # "is not None" matters: the ITS value is 0, which is falsy in Python
        return self.primer is not None

    def extra_args(self) -> list[str]:
        """Arguments that follow the primer mode: run.sh <primer> <taxonomy> <database>"""
        return [str(self.taxonomy_mode), str(self.database_mode)]

    def set_enabled(self, enabled: bool) -> None:
        """Lock or unlock all dropdowns (used while the pipeline runs)."""
        for select in (self._primer_select, self._taxonomy_select, self._database_select):
            select.set_enabled(enabled)