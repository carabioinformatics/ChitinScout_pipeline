"""Starts and stops the pipeline bash scripts. Contains no GUI code."""
import asyncio
import os
import signal
from pathlib import Path
from typing import Callable, Optional, Sequence

# Folder containing run.sh, ITSrun.sh and TEFrun.sh
SCRIPT_DIR = Path(__file__).resolve().parent


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
        on_start: Optional[Callable[[], None]] = None,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> int:
        """Run ./run.sh <primer_mode> [extra_args...] and return its exit code."""
        self._stopped_by_user = False
        self._process = await asyncio.create_subprocess_exec(
            "bash", "./run.sh", str(primer_mode), *extra_args,
            cwd=SCRIPT_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
            # Own process group, so stop() can end the scripts AND
            # every program they started (python, blast, ...)
            start_new_session=True,
        )
        if on_start:
            on_start()

        try:
            async for raw_line in self._process.stdout:
                if on_output:
                    on_output(raw_line.decode(errors="replace").rstrip())
            return await self._process.wait()
        finally:
            self._process = None

    async def stop(self, timeout: float = 5.0) -> None:
        """Stop the running pipeline. Does nothing if nothing is running."""
        process = self._process
        if process is None or process.returncode is not None:
            return

        self._stopped_by_user = True
        self._signal_group(process, signal.SIGTERM)       # ask nicely
        try:
            await asyncio.wait_for(process.wait(), timeout)
        except asyncio.TimeoutError:
            self._signal_group(process, signal.SIGKILL)   # force it
            await process.wait()

    @staticmethod
    def _signal_group(process: asyncio.subprocess.Process, sig: int) -> None:
        try:
            # Because of start_new_session, the group id equals the process id
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass   # already finished