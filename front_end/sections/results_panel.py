"""Results panel: the top BLAST hits for one sample, shown below the status table."""
from pathlib import Path
from html import escape
from typing import Optional
import re
from nicegui import ui
from back_end.results import ResultsNotFound, find_input_files, load_top_results
from front_end.components.text_comp import text
from back_end.accepted_species import add_accepted

_HIT_LINE = re.compile(r"^Accession:\s*(\S+)\s+Sequence:\s*(\S+)\s*$")

# Fields of the table
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

# Styling to colour table row when that hit is a RefSeq
REF_SEQ_SLOT = r"""
    <q-tr :props="props" :class="(props.row.accession || '').includes('_') ? 'bg-green-1' : ''">
        <q-td auto-width>
            <q-checkbox v-model="props.selected" dense />
        </q-td>
        <q-td v-for="col in props.cols" :key="col.name" :props="props"
              :class="col.name === 'actions' ? 'text-center' : ''">
            <template v-if="col.name === 'actions'">
                <template v-if="!props.row.decision">
                    <q-btn flat dense no-caps color="positive" icon="check" label="Accept"
                        @click="() => $parent.$emit('decide', {id: props.row.id, decision: 'accepted'})" />
                    <q-btn flat dense no-caps color="negative" icon="close" label="Decline"
                        @click="() => $parent.$emit('decide', {id: props.row.id, decision: 'declined'})" />
                </template>
                <span v-else :class="props.row.decision === 'accepted' ? 'text-positive' : 'text-grey-6'">
                    {{ props.row.decision === 'accepted' ? 'Already accepted' : 'Already declined' }}
                </span>
            </template>
            <template v-else>
                {{ col.value }}
            </template>
        </q-td>
    </q-tr>
"""

# Styling for alignment section
ALIGN_CSS = """
.aln-scroll { overflow-x: auto; border: 1px solid #ddd; border-radius: 6px; padding: 8px 0; }
.aln-inner  { width: max-content; font-family: ui-monospace, Menlo, Consolas, monospace;
              font-size: 13px; line-height: 1.6; }
.aln-row    { display: flex; white-space: pre; }
.aln-name   { position: sticky; left: 0; z-index: 1; background: #fff; min-width: 150px;
              padding: 0 12px; font-weight: 600; }
.nt-a   { background: #2e9e4f; color: #fff; }   /* A green  */
.nt-t   { background: #e53935; color: #fff; }   /* T red    */
.nt-g   { background: #1e5bd8; color: #fff; }   /* G blue   */
.nt-c   { background: #e0a800; color: #fff; }   /* C yellow */
.nt-gap { background: #fff;    color: #000; }   /* gap      */
.nt-odd { background: #e91e8c; color: #fff; }   /* unusual letters (N, R, Y, ...) */
.nt-mm  { background: #7b1fa2; color: #fff; }   /* mismatch vs query */
"""

NT_CLASS = {"A": "nt-a", "T": "nt-t", "U": "nt-t", "G": "nt-g", "C": "nt-c", "-": "nt-gap"}

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
            text("Note: If an entry is highlighted with green, then it means that hit is also part of the RefSeq database. This could potentially be viewed as a very trustworthy hit.","label")
            text("The decision column is used to document which hits you choose as the most likely answer for all of the samples you processed during this session. All of your choices will be saved to an Excel sheet and saved to your session's output folder.", "body")
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
                table = ui.table(columns=COLUMNS, rows=rows, row_key="id", selection="multiple").props(
                    "flat bordered dense"
                ).classes("w-full")
                table.add_slot("body", REF_SEQ_SLOT)                
                table.on("decide", lambda e: self._decide(e.args, table, rows, sample, output_dir))

                alignment_box = ui.column().classes("w-full gap-2")
                alignment_box.set_visibility(False)
                ui.button(
                    "Make alignment with selected sequences", icon="align_horizontal_left",
                    on_click=lambda: self._make_alignment(table, sample, output_dir, alignment_box),
                )

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

    def _make_alignment(self, table, sample, output_dir, box) -> None:
        names = list(dict.fromkeys(row["accession"] for row in table.selected))
        if not names:
            ui.notify("Tick at least one hit first.", type="warning")
            return

        try:
            file_name = Path(output_dir) / f"{sample}/Final/INT26_{sample}_HIT_SEQUENCE_SUMMARY.txt"
            sequences = load_alignment(file_name)
        except OSError as problem:
            ui.notify(f"Could not read the alignment file: {problem}", type="negative")
            return
        if "query" not in sequences:
            ui.notify("The alignment file has no 'query' line.", type="negative")
            return

        missing = [n for n in names if n not in sequences]

        box.clear()
        box.set_visibility(True)
        with box:
            text("Alignment", "title")
            ui.label("Alignment").classes("text-lg font-medium")
            mode_toggle = ui.toggle(
                {"plain": "No colours", "colour": "Nucleotide colours", "mismatch": "Mismatches vs query"},
                value="mismatch",
            )
            if missing:
                ui.label(f"Not found in alignment file: {', '.join(missing)}").classes("text-amber-8")
            view = ui.html("", sanitize=False)

            def refresh() -> None:
                view.content = build_alignment_html(sequences, names, mode_toggle.value)

            mode_toggle.on_value_change(refresh)
            refresh()

    def hide(self) -> None:
        self._card.set_visibility(False)

def load_alignment(path: Path) -> dict[str, str]:
    """Lines look like: 'Accession: <name>\t\tSequence: <sequence>'. The query is named 'query'."""
    sequences: dict[str, str] = {}
    for line in Path(path).read_text().splitlines():
        match = _HIT_LINE.match(line.strip())
        if match:
            sequences[match.group(1)] = match.group(2)
    return sequences

def _char_class(mode: str, ch: str, query_ch: str, is_query: bool) -> str:
    ch, query_ch = ch.upper(), query_ch.upper()
    if mode == "plain":
        return ""
    if mode == "colour":
        return NT_CLASS.get(ch, "nt-odd")
    # mode == "mismatch": only differences from the QUERY get a background
    if not is_query and ch != query_ch:
        return "nt-mm"
    return ""

def render_sequence(seq: str, query: str, mode: str, is_query: bool = False) -> str:
    """Group neighbouring characters with the same style into one <span> (keeps the HTML small)."""
    parts, run, run_class = [], [], None
    for i, ch in enumerate(seq):
        query_ch = query[i] if i < len(query) else "-"
        cls = _char_class(mode, ch, query_ch, is_query)
        if cls != run_class and run:
            parts.append(f'<span class="{run_class}">{escape("".join(run))}</span>')
            run = []
        run_class = cls
        run.append(ch)
    if run:
        parts.append(f'<span class="{run_class}">{escape("".join(run))}</span>')
    return "".join(parts)

def build_alignment_html(sequences: dict[str, str], names: list[str], mode: str) -> str:
    query = sequences["query"]
    rows = [("query", query, True)] + [(n, sequences[n], False) for n in names if n in sequences]
    html = ['<div class="aln-scroll"><div class="aln-inner">']
    for name, seq, is_query in rows:
        html.append(
            f'<div class="aln-row"><span class="aln-name">{escape(name)}</span>'
            f'<span>{render_sequence(seq, query, mode, is_query)}</span></div>'
        )
    html.append("</div></div>")
    return "".join(html)