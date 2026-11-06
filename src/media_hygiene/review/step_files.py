"""The files `mh` and the home server share about a step, and what they say (0355)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.services.step_progress import read_progress, step_lost

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class WatchFiles:
    """The value of the variable, and the files `mh` and the server share."""

    # `MEDIA_HYGIENE_LAUNCHER_STEPS` of an `mh` that keeps the server up
    kept: str = "3"
    now: str = ".mh-step-now.json"  # a step to run now, the server still up
    # written by `mh`: the id of the step it runs
    running: str = ".mh-step-running.json"
    done: str = ".mh-step-done.json"  # written by `mh`: the id and the exit code
    cid: str = ".mh-home.cid"  # the home server's container id (`docker run --cidfile`)
    code: str = ".mh-home.code"  # its exit code, written by `docker wait`


WATCH: Final = WatchFiles()


class StepState:
    """What `GET /api/step` says, the values the page compares."""

    IDLE: Final = "idle"
    WAITING: Final = "waiting"  # written, not yet taken by `mh`
    RUNNING: Final = "running"
    DONE: Final = "done"


def read_state(folder: Path) -> dict[str, object]:
    """Read the files of the steps, the most advanced first.

    Args:
        folder: The reports folder.

    Returns:
        The state, its id and, once done, its exit code.
    """
    for name, state in (
        (WATCH.now, StepState.WAITING),
        (WATCH.running, StepState.RUNNING),
        (WATCH.done, StepState.DONE),
    ):
        said = _said(folder / name)
        if said is not None:
            found = {"state": state, "id": said.get("id"), "code": said.get("code")}
            progress = read_progress(folder)  # a step that writes says how far (0361)
            if state == StepState.RUNNING and step_lost(folder):
                found["lost"] = True  # its window closed: no more pulse (0632)
            return found if progress is None else found | {"progress": progress}
    return {"state": StepState.IDLE, "id": None, "code": None}


def _said(file: Path) -> dict[str, object] | None:
    """Read one file of the steps.

    Args:
        file: The file.

    Returns:
        What it says; None when absent or unreadable.
    """
    try:  # `-sig`: Windows PowerShell 5.1 may write a byte order mark.
        said = json.loads(file.read_text("utf-8-sig"))
    except OSError, ValueError:
        return None
    return said if isinstance(said, dict) else None
