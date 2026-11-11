import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
PRIMERS_FILE = CONFIG_DIR / "primers.json"

DEFAULT_PRIMERS = [
    {
        "label": "ITS1 + ITS4 primers",
        "forward_name": "ITS1",
        "reverse_name": "ITS4",
        "forward_suffix": "ITS1___1.ab1",
        "reverse_suffix": "ITS4___1.ab1",
    },
    {
        "label": "TEF forward and reverse primers",
        "forward_name": "TEF_forward",
        "reverse_name": "TEF_reverse",
        "forward_suffix": "TEF_forward___1.ab1",
        "reverse_suffix": "TEF_reverse___1.ab1",
    },
    {
        "label": "LSU forward and reverse primers",
        "forward_name": "LSU_forward",
        "reverse_name": "LSU_reverse",
        "forward_suffix": "LSU_forward___1.ab1",
        "reverse_suffix": "LSU_reverse___1.ab1",
    },
    {
        "label": "B-Tub forward and reverse primers",
        "forward_name": "B_Tub_forward",
        "reverse_name": "B_Tub_reverse",
        "forward_suffix": "B_Tub_forward_Primer__1.ab1",
        "reverse_suffix": "B_Tub_reverse_primer__1.ab1",
    },
]

REQUIRED_KEYS = {
    "label", "forward_name", "reverse_name", "forward_suffix", "reverse_suffix",
}


def _load_custom() -> list[dict]:
    """Read user-added primers. Missing or corrupt file -> empty list."""
    if not PRIMERS_FILE.exists():
        return []
    try:
        data = json.loads(PRIMERS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [p for p in data if isinstance(p, dict) and REQUIRED_KEYS <= p.keys()]


def _save_custom(primers: list[dict]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)  # creates Config/ if needed
    tmp = PRIMERS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(primers, indent=2), encoding="utf-8")
    tmp.replace(PRIMERS_FILE)  # write then swap, so a crash can't corrupt the file


def all_primers() -> list[dict]:
    """
        Defaults first, then user-added primers.
    """
    return DEFAULT_PRIMERS + _load_custom()


def primer_labels() -> dict[int, str]:
    """
        {index: label}, ready to pass to the dropdown.
    """
    return {i: p["label"] for i, p in enumerate(all_primers())}


def get_suffixes(index: int) -> tuple[str, str]:
    """
        Get the file ending for a primer pairing type.
    """
    p = all_primers()[index]
    return p["forward_suffix"], p["reverse_suffix"]


def add_primer(
    forward_name: str,
    reverse_name: str,
    forward_suffix: str,
    reverse_suffix: str,
) -> int:
    """
    Validate and save a new primer. Returns its index.
    Raises ValueError with a user-friendly message if something is wrong.
    """
    forward_name = forward_name.strip()
    reverse_name = reverse_name.strip()
    forward_suffix = forward_suffix.strip()
    reverse_suffix = reverse_suffix.strip()

    if not all((forward_name, reverse_name, forward_suffix, reverse_suffix)):
        raise ValueError("Please fill in all four fields.")
    if forward_suffix == reverse_suffix:
        raise ValueError("Forward and reverse suffixes must be different.")

    label = f"{forward_name} + {reverse_name} primers"
    existing = all_primers()
    if any(p["label"].lower() == label.lower() for p in existing):
        raise ValueError(f"'{label}' already exists.")

    custom = _load_custom()
    custom.append(
        {
            "label": label,
            "forward_name": forward_name,
            "reverse_name": reverse_name,
            "forward_suffix": forward_suffix,
            "reverse_suffix": reverse_suffix,
        }
    )
    _save_custom(custom)
    return len(existing)  # index of the newly added primer