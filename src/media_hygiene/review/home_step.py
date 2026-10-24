"""`POST /api/step`: end the home server so that `mh` runs the step chosen.

A step of `mh menu` is sent as its number and command, run only when the menu still
gives that command: its words go into the one-shot file when `mh` reads it (0354), and
the server ends as for a step with fields; else it ends with `STEP_EXIT_BASE + n`, and
`mh` reads step `n` from `mh menu`, a container of its own. A step with fields
is sent as its name and its values: they are checked, written into the one-shot file
(`home_fields`), and the server ends with `STEP_EXIT_BASE + FIELDS_STEP`. With an `mh`
that keeps the server up, a console step is handed over without ending (`step_watch`,
0355). Each needs
a JSON body: a page of another site cannot send one without the browser asking first.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.cli.menu_steps import full_catalog
from media_hygiene.i18n import _
from media_hygiene.review.home_fields import FieldError, checked_words, write_step
from media_hygiene.review.home_views import FIELDS_STEP, STEP_EXIT_BASE
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.step_watch import busy, keep_step, runs_beside
from media_hygiene.services.next_command import LAUNCHER_FUNCTION

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.ending import Ending
    from media_hygiene.review.home_views import HomeState
    from media_hygiene.review.http import Request


class _Chosen(BaseModel):
    """The step chosen: its number and command, or its name and its fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    number: int | None = None
    command: str = ""
    name: str = ""
    fields: dict[str, str] = Field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StepDoor:
    """What a step chosen needs: the state, the end, where the words go."""

    state: Callable[[], HomeState]
    ending: Ending
    reports_dir: Path
    relays_steps: bool = False  # `mh` runs the step `STEP_EXIT_BASE + n` names
    relays_fields: bool = False  # `mh` also runs the words of the one-shot file
    keeps: bool = False  # `mh` keeps the server up and runs a console step beside it


async def step_response(door: StepDoor, request: Request) -> Response:
    """End the server with the code of the step chosen, when it may run.

    Args:
        door: The state, the end, the reports folder, what `mh` relays.
        request: `POST /api/step`.

    Returns:
        The step about to run; 409 when the steps changed or `mh` would not run it,
        422 for a value refused (the server then keeps serving).
    """
    refused = refused_post(request)
    if refused is not None:
        return refused
    if not door.relays_steps:
        message = _("This mh does not run the steps of the page: type the command.")
        return json_response(HTTPStatus.CONFLICT, {"error": message})
    try:
        chosen = _Chosen.model_validate_json(request.body)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    pending = busy(door.reports_dir) if door.keeps else None
    if pending is not None:
        return pending
    if chosen.name:
        return await _with_fields(door, chosen)
    return await _numbered(door, chosen)


async def _numbered(door: StepDoor, chosen: _Chosen) -> Response:
    """Hand over a step of `mh menu`, when the menu still gives that command.

    Args:
        door: The state, the end, the reports folder, what `mh` relays.
        chosen: The step's number and command.

    Returns:
        The step about to run, or kept beside the server; 409 when the steps changed.
    """
    state = await asyncio.to_thread(door.state)
    number = chosen.number or 0
    command = state.command_of(number)
    if not number or command is None or command != chosen.command:
        message = _("The steps changed since the page was shown: here they are.")
        return json_response(HTTPStatus.CONFLICT, {"error": message})
    words = tuple(command.split())  # as `mh` splits `mh menu`'s line
    if words[:1] == (LAUNCHER_FUNCTION,):
        words = words[1:]
    if door.keeps and runs_beside(words):
        return await keep_step(door.reports_dir, words, command)
    door.ending.end(STEP_EXIT_BASE + await _handed(door, number, words))
    return json_response(HTTPStatus.OK, {"number": number, "command": command})


async def _handed(door: StepDoor, number: int, words: tuple[str, ...]) -> int:
    """Hand a step of the menu to `mh`: its words in the one-shot file when it reads it.

    `mh` then runs them at once, without running `mh menu` in a container of its own
    to learn which command step `n` is: 2.1 to 2.5 s per click (measured on Windows,
    0354). Else, or when the file cannot be written, its number, as before.

    Args:
        door: The reports folder, what `mh` relays.
        number: The step's number in `mh menu`.
        words: Its words, without `mh`.

    Returns:
        The code to end with, less `STEP_EXIT_BASE`.
    """
    if not door.relays_fields:
        return number
    try:
        await asyncio.to_thread(write_step, door.reports_dir, words)
    except OSError:
        return number
    return FIELDS_STEP


async def _with_fields(door: StepDoor, chosen: _Chosen) -> Response:
    """Check the words of a form, hand them to `mh`, then end.

    Args:
        door: The end, the reports folder, what `mh` relays.
        chosen: The step's name and values.

    Returns:
        The command about to run; 422 for a value refused, 409 when `mh` cannot
        take the words (the command to copy is sent instead).
    """
    try:
        step = full_catalog().step(chosen.name)
        words = checked_words(step, chosen.fields)
    except KeyError:
        return Response(HTTPStatus.BAD_REQUEST)
    except FieldError as error:
        return json_response(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(error)})
    command = shown(words)
    if not door.relays_fields:
        message = _("This mh does not take the words of a form: copy the command.")
        return json_response(
            HTTPStatus.CONFLICT, {"error": message, "command": command}
        )
    if door.keeps and runs_beside(words):
        return await keep_step(door.reports_dir, words, command)
    try:
        await asyncio.to_thread(write_step, door.reports_dir, words)
    except OSError:
        message = _("The reports folder cannot be written: copy the command.")
        return json_response(
            HTTPStatus.CONFLICT, {"error": message, "command": command}
        )
    door.ending.end(STEP_EXIT_BASE + FIELDS_STEP)
    return json_response(HTTPStatus.OK, {"command": command})


def shown(words: tuple[str, ...]) -> str:
    """The command as the user would type it, a value with a space quoted.

    Args:
        words: The command's words, without `mh`.

    Returns:
        E.g. `mh album "Noël 2025" --category Noël`.
    """
    quoted = (f'"{word}"' if " " in word or "\\" in word else word for word in words)
    return " ".join((LAUNCHER_FUNCTION, *quoted))
