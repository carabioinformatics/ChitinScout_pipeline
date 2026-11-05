from enum import Enum
from pathlib import Path
from back_end.ui_assisting_files.file_pairing import INPUT_DIR

ALLOWED_EXTENSION = ".ab1"

class Outcome(Enum):
    ADDED = "added"
    REPLACED = "replaced"
    REJECTED = "rejected"

def store_input_file(
    file_name: str, content: bytes, input_dir: Path = INPUT_DIR
) -> tuple[Outcome, str]:
    """
        Save one file into the input folder.
        Returns the outcome and a message suitable for the output log.
    """
    base_name = Path(file_name.replace("\\", "/")).name

    if not base_name.lower().endswith(ALLOWED_EXTENSION):
        return Outcome.REJECTED, f"Skipped {base_name or file_name}: not an {ALLOWED_EXTENSION} file"
    if not content:
        return Outcome.REJECTED, f"Skipped {base_name}: file is empty"

    # Normalise the extension to lowercase
    safe_name = base_name[: -len(ALLOWED_EXTENSION)] + ALLOWED_EXTENSION

    input_dir.mkdir(parents=True, exist_ok=True)
    target = input_dir / safe_name
    existed = target.exists()

    # Write to a temporary file first and then rename it
    temporary = input_dir / (safe_name + ".part")
    temporary.write_bytes(content)
    temporary.replace(target)

    if existed:
        return Outcome.REPLACED, f"Replaced existing file: {safe_name}"
    return Outcome.ADDED, f"Added: {safe_name}"


def count_input_files(input_dir: Path = INPUT_DIR) -> int:
    if not input_dir.is_dir():
        return 0
    return sum(1 for _ in input_dir.glob(f"*{ALLOWED_EXTENSION}"))