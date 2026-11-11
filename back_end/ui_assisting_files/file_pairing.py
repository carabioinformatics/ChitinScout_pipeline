from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from back_end.ui_assisting_files.primer_store import get_suffixes

# File path to input folder
INPUT_DIR = Path(__file__).resolve().parent.parent / "Input"

# Different primer options
# PRIMER_SUFFIXES = {
#     0: ("ITS1___1.ab1", "ITS4___1.ab1"),
#     1: ("TEF_forward___1.ab1", "TEF_reverse___1.ab1"), 
#     2: ("LSU_forward___1.ab1", "LSU_reverse___1.ab1"),
#     3: ("B_Tub_forward_Primer__1.ab1", "B_Tub_reverse_primer__1.ab1"),
# }

@dataclass
class UnpairedFile:
    file_name: str
    missing: str  # Either forward/reverse/none

@dataclass
class PairingResult:
    samples: list[str]              # sample names that have both files
    unpaired: list[UnpairedFile]    # files whose partner is missing
    unrecognised: list[str]         # .ab1 files that fit neither ending

def sample_name_from(file_name: str) -> Optional[str]:
    """
        Copy on the sample name from the file.
    """
    parts = file_name.split("_")
    return parts[1] if len(parts) > 1 else None


def find_pairs(primer_mode: int, input_dir: Path = INPUT_DIR) -> PairingResult:
    """
        Finds all the file pairs in the input directory that have the specified
        primer information included. Makes list of all unrecognised files, forward files,
        reverse files and unpaired files.
    """
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input folder not found: {input_dir}")

    forward_suffix, reverse_suffix = get_suffixes(primer_mode)
    forwards: dict[str, str] = {}
    reverses: dict[str, str] = {}
    unrecognised: list[str] = []

    for path in sorted(input_dir.glob("*.ab1")):
        name = path.name
        sample = sample_name_from(name)
        if sample is None:
            unrecognised.append(name)
        elif name.endswith(forward_suffix):
            forwards[sample] = name
        elif name.endswith(reverse_suffix):
            reverses[sample] = name
        else:
            unrecognised.append(name)

    unpaired = (
        [UnpairedFile(forwards[s], "reverse") for s in sorted(forwards.keys() - reverses.keys())]
        + [UnpairedFile(reverses[s], "forward") for s in sorted(reverses.keys() - forwards.keys())]
    )

    return PairingResult(
        samples=sorted(forwards.keys() & reverses.keys()),
        unpaired=unpaired,
        unrecognised=unrecognised,
    )