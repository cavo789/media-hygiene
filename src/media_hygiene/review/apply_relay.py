"""How *Apply now* hands its step to `mh` (0363): beside the server, words, a number.

- kept up (`MEDIA_HYGIENE_LAUNCHER_STEPS=3`) and the page served by the home server
  itself (browse, 0356): the words of `clean --decisions` go into `.mh-step-now.json`
  (`step_watch.keep_step`); the server stays up and the page follows the step on
  `GET /api/step`;
- an `mh` that reads the one-shot file (`2`, or `3` for a review served by a container
  of its own): its words in `.mh-step.json`, the server ending with the fields code,
  without running `mh menu` to learn which command step `n` is (2.1 to 2.5 s, measured
  on Windows, step 35b of `mh-measure.ps1`);
- else, or the folder not writable: `STEP_EXIT_BASE + n`, as before.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.review.home_fields import RELAY_FIELDS, write_step
from media_hygiene.review.home_views import FIELDS_STEP, STEP_EXIT_BASE
from media_hygiene.review.serving import json_response
from media_hygiene.review.step_watch import WATCH, keep_step, keeps_server
from media_hygiene.services.next_command import (
    LAUNCHER_FUNCTION,
    LAUNCHER_STEPS_VARIABLE,
)

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.apply_api import ApplyStep
    from media_hygiene.review.ending import Ending
    from media_hygiene.review.http import Response


@dataclass(frozen=True, slots=True)
class ApplyRelay:
    """Where the words of the step go, and whether the server stays up meanwhile."""

    reports_dir: Path
    beside: bool = False  # served by the home server, which `mh` may keep up


def home_relay(reports_dir: Path) -> ApplyRelay:
    """The relay of a page the home server serves: beside it when `mh` keeps it up.

    Args:
        reports_dir: The reports folder.

    Returns:
        The relay.
    """
    return ApplyRelay(reports_dir, beside=keeps_server())


async def relayed(
    relay: ApplyRelay | None, step: ApplyStep, ending: Ending
) -> Response:
    """Hand the step to `mh` the fastest way it takes.

    Args:
        relay: The reports folder and whether the server may stay up; None: a number.
        step: Its number in `mh menu` and its full command, `mh` included.
        ending: Ends the server when the step does not run beside it.

    Returns:
        The step: `kept` with its id when it runs beside the server.
    """
    number, command = step.number, step.command
    words = tuple(command.split())  # as `mh` splits `mh menu`'s line
    if words[:1] == (LAUNCHER_FUNCTION,):
        words = words[1:]
    mode = os.environ.get(LAUNCHER_STEPS_VARIABLE)
    if relay is not None and relay.beside and mode == WATCH.kept:
        return await keep_step(relay.reports_dir, words, command)
    code = STEP_EXIT_BASE + number
    if relay is not None and mode in {RELAY_FIELDS, WATCH.kept}:
        with contextlib.suppress(OSError):  # not writable: the number, as before
            await asyncio.to_thread(write_step, relay.reports_dir, words)
            code = STEP_EXIT_BASE + FIELDS_STEP
    ending.end(code)
    return json_response(HTTPStatus.OK, {"number": number, "command": command})
