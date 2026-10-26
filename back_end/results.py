"""Reads a sample's top BLAST results from the run's output folder. No GUI code."""
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from back_end.file_pairing import INPUT_DIR, PRIMER_SUFFIXES

# ASSUMPTION: where the results file sits inside <run output>/<sample>/.
# Adjust to match your pipeline.
RESULTS_FILE_PATTERN = "Final/INT26_{sample}_BLAST_SUMMARY_NCBI.txt"

# How many hits to show per sample
TOP_N = 25

# Accepted header names for each field (compared case-insensitively, ignoring
# punctuation, so "Coverage (%)" matches "coverage")
LINE_PATTERN = re.compile(
    r"Accession:\s*(?P<accession>\S+)\s+"
    r"Species:\s*(?P<species>.*?)\s+"
    r"E-value:\s*(?P<evalue>\S+)\s+"
    r"%Identity:\s*(?P<identity>\S+)\s+"
    r"%Coverage:\s*(?P<coverage>\S+)"
)

class ResultsNotFound(Exception):
    """The results file does not exist (yet) or could not be understood."""

@dataclass
class BlastHit:
    accession: str
    species: str
    coverage: Optional[float]   # percent
    identity: Optional[float]   # percent

def _to_number(value: str) -> Optional[float]:
    try:
        return float(value.strip().rstrip("%"))
    except ValueError:
        return None

def load_top_results(
    output_dir: Path, sample: str, limit: int = TOP_N
) -> tuple[Path, list[BlastHit]]:
    """Return the results file used and the first `limit` hits in it.

    The hits are shown in file order, so the order your pipeline wrote
    them in is the ranking the user sees."""
    sample_dir = output_dir / sample
    pattern = RESULTS_FILE_PATTERN.format(sample=sample)
    matches = sorted(sample_dir.rglob(pattern)) if sample_dir.is_dir() else []
    if not matches:
        raise ResultsNotFound(
            f"No file matching '{pattern}' was found in {sample_dir}"
        )
    path = matches[0]

    lines = [
        line
        for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        if line.strip()
    ]
    if not lines:
        raise ResultsNotFound(f"{path.name} is empty")

    hits: list[BlastHit] = []
    for line in lines:
        match = LINE_PATTERN.search(line)
        if not match:
            continue   # skip anything that is not a hit line (headers, notes, ...)
        hits.append(
            BlastHit(
                accession=match["accession"],
                species=match["species"].strip(),
                coverage=_to_number(match["coverage"]),
                identity=_to_number(match["identity"]),
            )
        )
        if len(hits) >= limit:
            break

    if not hits:
        raise ResultsNotFound(
            f"{path.name} contains no lines in the expected "
            f"'Accession: ... Species: ... %Identity: ... %Coverage: ...' format"
        )
    return path, hits


def find_input_files(
    sample: str, primer_mode: int, input_dir: Path = INPUT_DIR
) -> tuple[Optional[str], Optional[str]]:
    """Names of the forward and reverse input files for a sample (None if absent)."""
    forward_suffix, reverse_suffix = PRIMER_SUFFIXES[primer_mode]
    forward = next(iter(sorted(input_dir.glob(f"*_{sample}_{forward_suffix}"))), None)
    reverse = next(iter(sorted(input_dir.glob(f"*_{sample}_{reverse_suffix}"))), None)
    return (forward.name if forward else None, reverse.name if reverse else None)