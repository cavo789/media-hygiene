r"""The steps `mh` runs while the home server stays up (0355).

An `mh` that watches (`MEDIA_HYGIENE_LAUNCHER_STEPS=3`) starts the home server in the
background, then looks for `.mh-step-now.json` in the reports folder four times a
second. A console step chosen on the page (`clean`, `status`…) is written there with an
id, and the server keeps serving: `mh` removes the file, writes `.mh-step-running.json`
(the id), runs the step in its window, its questions there, then writes
`.mh-step-done.json` (the id and the exit code). `GET /api/step` tells the page where
its step is. A step that opens a page still ends the server (`.mh-step.json`, 0354):
the page needs the port until it is served by the home server itself (0356).
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
from dataclasses import dataclass
from http import HTTPStatus
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.safety import PAGE_COMMANDS
from media_hygiene.i18n import _
from media_hygiene.review.serving import json_response
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.search.folders import BROWSE_PATH
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Response


@dataclass(frozen=True, slots=True)
class WatchFiles:
    """The value of the variable, and the files `mh` and the server share."""

    kept: str = (
        "3"  # `MEDIA_HYGIENE_LAUNCHER_STEPS` of an `mh` that keeps the server up
    )
    now: str = ".mh-step-now.json"  # a step to run now, the server still up
    running: str = (
        ".mh-step-running.json"  # written by `mh`: the id of the step it runs
    )
    done: str = ".mh-step-done.json"  # written by `mh`: the id and the exit code
    cid: str = ".mh-home.cid"  # the home server's container id (`docker run --cidfile`)
    code: str = ".mh-home.code"  # its exit code, written by `docker wait`


WATCH: Final = WatchFiles()
STEP_PATH: Final = "/api/step"  # `POST` a step (`home_step`), `GET` where it is
# The pages the home server serves itself (0356): a click on them is a plain link.
SERVED_HERE: Final[MappingProxyType[tuple[str, ...], str]] = MappingProxyType(
    {("search",): SEARCH_PAGE_PATH, ("browse",): BROWSE_PATH}
)
_ID_BYTES: Final = 6


class StepState:
    """What `GET /api/step` says, the values the page compares."""

    IDLE: Final = "idle"
    WAITING: Final = "waiting"  # written, not yet taken by `mh`
    RUNNING: Final = "running"
    DONE: Final = "done"


def keeps_server() -> bool:
    """Tell whether `mh` keeps the server up and runs the steps beside it.

    Returns:
        True when `MEDIA_HYGIENE_LAUNCHER_STEPS` is `3`.
    """
    return os.environ.get(LAUNCHER_STEPS_VARIABLE) == WATCH.kept


def served_here(words: tuple[str, ...]) -> str | None:
    """The path of a page the home server serves itself, for a step's words.

    Args:
        words: The command's words, without `mh`.

    Returns:
        `/search` or `/browse`; None for any other step (with options, too).
    """
    return SERVED_HERE.get(words)


def runs_beside(words: tuple[str, ...]) -> bool:
    """Tell whether a step runs while the server stays up: not one opening a page.

    Args:
        words: The command's words, without `mh`.

    Returns:
        True for a console step.
    """
    return bool(words) and words[0] not in PAGE_COMMANDS


def busy(folder: Path) -> Response | None:
    """Refuse a step while another waits or runs in the window of `mh`.

    Args:
        folder: The reports folder.

    Returns:
        409 with the reason, or None when no step is pending.
    """
    if (folder / WATCH.now).exists() or (folder / WATCH.running).exists():
        message = _("A step is running in the window of mh: wait for its end.")
        return json_response(HTTPStatus.CONFLICT, {"error": message})
    return None


async def keep_step(folder: Path, words: tuple[str, ...], command: str) -> Response:
    """Hand a console step to `mh`, the server staying up.

    Args:
        folder: The reports folder.
        words: The command's words, without `mh`.
        command: The command as the page shows it.

    Returns:
        Its id and command, to follow it on `GET /api/step`; 409 when a step is
        waiting or running, or when the folder cannot be written.
    """
    refused = busy(folder)
    if refused is not None:
        return refused
    step = secrets.token_hex(_ID_BYTES)
    text = json.dumps({"id": step, "words": list(words)}, ensure_ascii=False, indent=0)
    try:
        await asyncio.to_thread((folder / WATCH.now).write_text, text + "\n", "utf-8")
    except OSError:
        message = _("The reports folder cannot be written: copy the command.")
        return json_response(HTTPStatus.CONFLICT, {"error": message})
    answer = {"id": step, "command": command, "kept": True, "follow": STEP_PATH}
    return json_response(HTTPStatus.OK, answer)


async def step_state(folder: Path) -> Response:
    """Say where the last step is: waiting, running, done (its exit code), or none.

    Args:
        folder: The reports folder.

    Returns:
        `{"state": …, "id": …, "code": …}`.
    """
    return json_response(HTTPStatus.OK, await asyncio.to_thread(_state, folder))


def _state(folder: Path) -> dict[str, object]:
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
        try:
            # `-sig`: Windows PowerShell 5.1 may write a byte order mark.
            said = json.loads((folder / name).read_text("utf-8-sig"))
        except OSError, ValueError:
            continue
        if isinstance(said, dict):
            return {"state": state, "id": said.get("id"), "code": said.get("code")}
    return {"state": StepState.IDLE, "id": None, "code": None}
