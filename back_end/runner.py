"""Starts and stops the pipeline bash scripts. Contains no GUI code."""
import asyncio
import os
import re
import signal
import tempfile
from pathlib import Path
from typing import Callable, Optional, Sequence
from back_end.user_config import get_email

# Folder containing run.sh, ITSrun.sh and TEFrun.sh
SCRIPT_DIR = Path(__file__).resolve().parent
# Environment variable the bash scripts read the sample list file from
SAMPLE_LIST_ENV_VAR = "SAMPLE_LIST_FILE"

PROGRESS_PATTERN = re.compile(r"\((\d+)/(\d+) samples\)")
PLOT_PATTERN = re.compile(r"^PLOT_FILE:\s*(.+)$")
# Marker lines printed by the pipeline scripts (see pipeline_status.py)
STEP_PATTERN = re.compile(r"^@@STEP\|([^|]*)\|([^|]*)\|([^|]*)\|?(.*)$")
SAMPLE_ERROR_PATTERN = re.compile(r"^@@SAMPLE_ERROR\|([^|]*)\|(.*)$")
OUTPUT_DIR_PATTERN = re.compile(r"^@@OUTPUT_DIR\|(.+)$")

class PipelineRunner:
    """Runs ./run.sh and can stop it, including everything it started."""

    def __init__(self) -> None:
        self._process: Optional[asyncio.subprocess.Process] = None
        self._stopped_by_user = False

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    @property
    def was_stopped(self) -> bool:
        """True if the last run ended because stop() was called."""
        return self._stopped_by_user

    async def run(
        self,
        primer_mode: int,
        extra_args: Sequence[str] = (),
        sample_names: Optional[Sequence[str]] = None,
        on_start: Optional[Callable[[], None]] = None,
        on_output: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_plot: Optional[Callable[[Path], None]] = None,
        on_step: Optional[Callable[[str, str, str, str], None]] = None,
        on_sample_error: Optional[Callable[[str, str], None]] = None,
        on_output_dir: Optional[Callable[[Path], None]] = None      
    ) -> int:
        """Run ./run.sh <primer_mode> [extra_args...] and return its exit code."""
        self._stopped_by_user = False

        env = {**os.environ, "PYTHONUNBUFFERED": "1"}
        sample_list_path = self._write_sample_list(sample_names)
        if sample_list_path:
            env[SAMPLE_LIST_ENV_VAR] = sample_list_path

        try:
            self._process = await asyncio.create_subprocess_exec(
                "bash", "./run.sh", str(primer_mode), *extra_args,
                cwd=SCRIPT_DIR,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
                start_new_session=True,
            )
            if on_start:
                on_start()

            async for raw_line in self._process.stdout:
                # The script's progress line starts with a carriage return
                line = raw_line.decode(errors="replace").rstrip().lstrip("\r")
                step_match = STEP_PATTERN.match(line)
                if step_match:
                    if on_step:
                        on_step(*step_match.groups())
                    continue
                error_match = SAMPLE_ERROR_PATTERN.match(line)
                if error_match:
                    if on_sample_error:
                        on_sample_error(*error_match.groups())
                    continue  
                dir_match = OUTPUT_DIR_PATTERN.match(line)
                if dir_match:
                    if on_output_dir:
                        on_output_dir((SCRIPT_DIR/dir_match.group(1)).resolve())
                    continue
                              
                if on_output:
                    on_output(line)
                if on_progress:
                    match = PROGRESS_PATTERN.search(line)
                    if match:
                        on_progress(int(match.group(1)), int(match.group(2)))
                if on_plot:
                    plot_match = PLOT_PATTERN.match(line)
                    if plot_match:
                        # The path is relative to the folder the scripts run in
                        on_plot((SCRIPT_DIR / plot_match.group(1)).resolve())
            return await self._process.wait()
        finally:
            self._process = None
            if sample_list_path:
                Path(sample_list_path).unlink(missing_ok=True)

    async def stop(self, timeout: float = 5.0) -> None:
        """Stop the running pipeline. Does nothing if nothing is running."""
        process = self._process
        if process is None or process.returncode is not None:
            return

        self._stopped_by_user = True
        self._signal_group(process, signal.SIGTERM)
        try:
            await asyncio.wait_for(process.wait(), timeout)
        except asyncio.TimeoutError:
            self._signal_group(process, signal.SIGKILL)   # force it
            await process.wait()

    @staticmethod
    def _write_sample_list(sample_names: Optional[Sequence[str]]) -> Optional[str]:
        """Write one sample name per line to a temp file and return its path."""
        if not sample_names:
            return None
        with tempfile.NamedTemporaryFile(
            "w", prefix="samples_", suffix=".txt", delete=False
        ) as file:
            file.write("\n".join(sample_names) + "\n")
            return file.name
        
    @staticmethod
    def _signal_group(process: asyncio.subprocess.Process, sig: int) -> None:
        try:
            # Because of start_new_session, the group id equals the process id
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass   # already finished