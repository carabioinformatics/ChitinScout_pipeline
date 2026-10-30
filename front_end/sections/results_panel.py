"""Results panel: the top BLAST hits for one sample, shown below the status table."""
from pathlib import Path
from typing import Optional
from nicegui import ui
from back_end.results import ResultsNotFound, find_input_files, load_top_results
from front_end.components.text_comp import text
from back_end.accepted_species import add_accepted

COLUMNS = [
    {"name": "accession", "label": "Accession number", "field": "accession",
     "align": "left", "sortable": True},
    {"name": "species", "label": "Species name", "field": "species",
     "align": "left", "sortable": True},
    {"name": "coverage", "label": "Coverage (%)", "field": "coverage",
     "align": "right", "sortable": True},
    {"name": "identity", "label": "Identity (%)", "field": "identity",
     "align": "right", "sortable": True},
    {"name": "actions", "label": "Decision", "field": "decision", "align": "center"},
]

ACTIONS_SLOT = r"""
<q-td :props="props" class="text-center">
  <template v-if="!props.row.decision">
    <q-btn flat dense no-caps color="positive" icon="check" label="Accept"
           @click="() => $parent.$emit('decide', {id: props.row.id, decision: 'accepted'})" />
    <q-btn flat dense no-caps color="negative" icon="close" label="Decline"
           @click="() => $parent.$emit('decide', {id: props.row.id, decision: 'declined'})" />
  </template>
  <span v-else :class="props.row.decision === 'accepted' ? 'text-positive' : 'text-grey-6'">
    {{ props.row.decision === 'accepted' ? 'Already accepted' : 'Already declined' }}
  </span>
</q-td>
"""

class ResultsPanel:
    """A card that is hidden until show() is called."""

    def __init__(
            self,
            accepted_species_file_name: str,
        ) -> None:
        self._accepted_species_file_name = accepted_species_file_name
        self._card = ui.card().classes("w-full rounded-xl shadow-md p-6 gap-4")
        with self._card:
            self._content = ui.column().classes("w-full gap-4")
        self._card.set_visibility(False)
        self._decisions: dict[tuple[str, str, str], str] = {}

    def show(
        self,
        sample: str,
        output_dir: Optional[Path],
        primer_mode: int,
        primer_label: str,
    ) -> None:
        self._content.clear()

        # Everything that can go wrong happens here, before any UI is built
        error = None
        results_path, hits = None, []
        if output_dir is None:
            error = "The output folder of this run is not known."
        else:
            try:
                results_path, hits = load_top_results(output_dir, sample)
            except ResultsNotFound as problem:
                error = str(problem)

        forward, reverse = find_input_files(sample, primer_mode)

        with self._content:
            # ---- Header: which sample is being viewed
            text("Top BLAST results for sample", "label")
            text(sample, "title")
            details = [
                ("Primer", primer_label),
                ("Forward file", forward or "not found"),
                ("Reverse file", reverse or "not found"),
                ("Results file", results_path.name if results_path else "not found"),
                ("Hits shown", str(len(hits))),
            ]
            with ui.grid(columns="auto 1fr").classes("gap-x-6 gap-y-1"):
                for label, value in details:
                    text(label, "label")
                    text(value, "body")

            # ---- Table (or the reason there isn't one)
            if error:
                with ui.row().classes("items-center gap-2 rounded-lg bg-amber-50 p-3 w-full"):
                    ui.icon("warning", color="warning")
                    text(error, "body")
            elif not hits:
                text("The results file contains no hits.", "body")
            else:
                rows = [
                    {
                        "id": index,
                        "accession": hit.accession,
                        "species": hit.species,
                        "coverage": round(hit.coverage, 1) if hit.coverage is not None else "",
                        "identity": round(hit.identity, 1) if hit.identity is not None else "",
                        "decision": self._decisions.get((sample, hit.accession, hit.species), ""),                    
                    }
                    for index, hit in enumerate(hits)
                ]
                table = ui.table(columns=COLUMNS, rows=rows, row_key="id").props(
                    "flat bordered dense"
                ).classes("w-full")
                table.add_slot("body-cell-actions", ACTIONS_SLOT)
                table.on("decide", lambda e: self._decide(e.args, table, rows, sample, output_dir))

        self._card.set_visibility(True)

    def _decide(self, args: dict, table: ui.table, rows: list[dict],
                sample: str, output_dir: Path) -> None:
        row = rows[args["id"]]
        if row["decision"]:
            return
        decision = args["decision"]

        if decision == "accepted":
            try:
                added = add_accepted(output_dir/self._accepted_species_file_name, sample, row["species"])
            except PermissionError:
                ui.notify(f"Cannot write to {self._accepted_species_file_name}. Is it open in Excel?", type="negative")
                return
            except Exception as problem:
                ui.notify(f"Could not save: {problem}", type="negative")
                return
            if not added:
                ui.notify(f"{row['species']} was already saved for {sample}.", type="info")
        row["decision"] = decision
        self._decisions[(sample, row["accession"], row["species"])] = decision
        table.rows[:] = rows
        table.update()

    def hide(self) -> None:
        self._card.set_visibility(False)