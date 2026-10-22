"""Starts the pipeline bash scripts. Contains no GUI code."""
import asyncio
import os
from pathlib import Path
from typing import Callable, Optional, Sequence

# Folder containing run.sh, ITSrun.sh and TEFrun.sh
SCRIPT_DIR = Path(__file__).resolve().parent


async def run_pipeline(
    primer_mode: int,
    extra_args: Sequence[str] = (),
    on_start: Optional[Callable[[], None]] = None,
    on_output: Optional[Callable[[str], None]] = None,
) -> int:
    """Run ./run.sh <primer_mode> [extra_args...] and return its exit code.

    primer_mode: 0 = ITS, 1 = TEF
    on_start:    called once the process has launched
    on_output:   called with every line the script prints
    """
    process = await asyncio.create_subprocess_exec(
        "bash", "./run.sh", str(primer_mode), *extra_args,
        cwd=SCRIPT_DIR,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,   # merge errors into the same stream
        # Stops Python scripts inside the pipeline from buffering their output,
        # so lines appear in the GUI as they happen
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    if on_start:
        on_start()

    async for raw_line in process.stdout:
        if on_output:
            on_output(raw_line.decode(errors="replace").rstrip())

    return await process.wait()