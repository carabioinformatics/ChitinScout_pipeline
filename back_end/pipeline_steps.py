"""The pipeline stages, in order. Used by the runner and the UI."""

# (step id used in marker lines, label shown in the table header)
STEPS = [
    ("trimming", "Trimming"),
    ("alignment", "Alignment"),
    ("consensus", "Consensus creation"),
    ("blast", "BLAST search"),
    ("summary", "BLAST summary report"),
    ("interpretation", "Result interpretation"),
]