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
from http import HTTPStatus
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.safety import PAGE_CAPTURED, PAGE_COMMANDS
from media_hygiene.i18n import _
from media_hygiene.review.home_fields import write_whole
from media_hygiene.review.served_more import SERVED_MORE, purge_step_page
from media_hygiene.review.serving import json_response
from media_hygiene.review.step_files import WATCH, StepState, WatchFiles, read_state
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from media_hygiene.services.step_progress import forget_progress

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Response


NEAR_REVIEW_PAGE: Final = "/review/near/"  # `services/review_here`
DISK_PAGE: Final = "/disk-space/"  # `services/disk_here` (0539)
HISTORY_PAGE: Final = "/history/"  # `services/history_here` (0350)
PAIRS_PAGE: Final = "/review/pairs/"  # `services/review_kinds` (0417), + the next 3
JUNK_PAGE: Final = "/review/junk/"
GONE_PAGE: Final = "/review/gone/"
BURSTS_PAGE: Final = "/review/bursts/"
PLACES_PAGE: Final = "/places/"  # `services/places_here` (0417)
STEP_PATH: Final = "/api/step"  # `POST` a step (`home_step`), `GET` where it is
# The pages the home server serves itself (0356): a click on them is a plain link.
SERVED_HERE: Final[MappingProxyType[tuple[str, ...], str]] = MappingProxyType(
    {
        ("library",): SEARCH_PAGE_PATH,
        **SERVED_MORE,
        ("review", "--near"): NEAR_REVIEW_PAGE,  # 0357
        ("review", "--pairs"): PAIRS_PAGE,  # 0417, as the next three
        ("review", "--junk"): JUNK_PAGE,
        ("review", "--gone"): GONE_PAGE,
        ("review",): BURSTS_PAGE,
        ("places",): PLACES_PAGE,
        ("history",): HISTORY_PAGE,  # 0350
        # `services/console_here`: what the step prints, in the page (0567)
        **{(name,): f"/console/{name}/" for name in PAGE_CAPTURED},
    }
)
_ID_BYTES: Final = 6
__all__ = ("WATCH", "StepState", "WatchFiles", "busy", "keep_step", "keeps_server")


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
        Its path; None for any other step (with options, too).
    """
    return SERVED_HERE.get(words) or purge_step_page(words)


def runs_beside(words: tuple[str, ...]) -> bool:
    """Tell whether a step runs while the server stays up: not one opening a page.

    Args:
        words: The command's words, without `mh`.

    Returns:
        True for a console step.
    """
    return bool(words) and words[0] not in PAGE_COMMANDS and "--pick" not in words


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
    await asyncio.to_thread(forget_progress, folder)
    step = secrets.token_hex(_ID_BYTES)
    text = json.dumps({"id": step, "words": list(words)}, ensure_ascii=False, indent=0)
    try:
        await asyncio.to_thread(write_whole, folder / WATCH.now, text + "\n")
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
    return json_response(HTTPStatus.OK, await asyncio.to_thread(read_state, folder))
