"""Results panel: the top BLAST hits for one sample, shown below the status table."""
from pathlib import Path
from typing import Optional

from nicegui import ui

from back_end.results import ResultsNotFound, find_input_files, load_top_results
from front_end.components.text_comp import text

COLUMNS = [
    {"name": "accession", "label": "Accession number", "field": "accession",
     "align": "left", "sortable": True},
    {"name": "species", "label": "Species name", "field": "species",
     "align": "left", "sortable": True},
    {"name": "coverage", "label": "Coverage (%)", "field": "coverage",
     "align": "right", "sortable": True},
    {"name": "identity", "label": "Identity (%)", "field": "identity",
     "align": "right", "sortable": True},
]


class ResultsPanel:
    """A card that is hidden until show() is called."""

    def __init__(self) -> None:
        self._card = ui.card().classes("w-full rounded-xl shadow-md p-6 gap-4")
        with self._card:
            self._content = ui.column().classes("w-full gap-4")
        self._card.set_visibility(False)

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
                    }
                    for index, hit in enumerate(hits)
                ]
                ui.table(columns=COLUMNS, rows=rows, row_key="id").props(
                    "flat bordered dense"
                ).classes("w-full")

        self._card.set_visibility(True)

    def hide(self) -> None:
        self._card.set_visibility(False)