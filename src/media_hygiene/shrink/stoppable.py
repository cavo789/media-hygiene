"""Run `ffmpeg` for `shrink --try` so that closing the page stops it at once (0307).

`scan.tool_run` waits for the end of a run; a draft takes about 30 s for a large clip
(estimated), and the page may close in the middle: here the process is polled, and
killed as soon as the run is asked to stop or takes too long.
"""

from __future__ import annotations

import subprocess  # fixed commands: ffmpeg with the files of the run
import tempfile
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import threading

_POLL_SECONDS: Final = 0.25
STOPPED: Final = "stopped"
_TOO_LONG: Final = "ffmpeg took more than {seconds:.0f} s"


def run_stoppable(
    command: tuple[str, ...], stop: threading.Event, seconds: float
) -> str | None:
    """Run a command to its end, unless asked to stop or too long.

    Args:
        command: The executable and its arguments.
        stop: Set when the run must end now.
        seconds: The time limit.

    Returns:
        None when it worked; `STOPPED` when stopped; else the last line it printed.
    """
    with (
        tempfile.TemporaryFile() as said,  # never a full pipe blocking ffmpeg
        subprocess.Popen(  # noqa: S603  # a fixed command, the run's files
            command, stdout=subprocess.DEVNULL, stderr=said
        ) as process,
    ):
        waited = 0.0
        while process.poll() is None:
            if stop.is_set() or waited > seconds:
                process.kill()
                process.wait()
                return STOPPED if stop.is_set() else _TOO_LONG.format(seconds=seconds)
            stop.wait(_POLL_SECONDS)
            waited += _POLL_SECONDS
        if process.returncode == 0:
            return None
        said.seek(0)
        lines = said.read().decode(errors="replace").strip().splitlines()
    return lines[-1] if lines else f"ffmpeg exit code {process.returncode}"
