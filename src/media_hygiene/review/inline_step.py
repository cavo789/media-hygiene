"""`POST /api/inline`: a short step run by the home server itself (0505).

A step flagged `inline` in the catalog (`config`, `backup`, `history`,
`reports --prune`) asks nothing and lasts seconds: the server runs it in a child
process with a time limit, and answers its console output as plain text, so that
the page shows it in a dialog and the user never leaves the browser. One at a time:
a second step while one runs is refused (409). A traceback never reaches the page:
only its last line, the error's message.
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.cli.menu_steps import full_catalog
from media_hygiene.i18n import _
from media_hygiene.review.home_fields import FieldError, checked_words, shown
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.services.next_command import LAUNCHER_FUNCTION

if TYPE_CHECKING:
    from media_hygiene.cli.menu_entry import Step
    from media_hygiene.review.http import Request

INLINE_SECONDS: Final = 120  # a step past it is stopped: the long ones have a page
_ANSI: Final = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_TRACEBACK: Final = "Traceback (most recent call last):"
_PLAIN: Final = {"NO_COLOR": "1", "TERM": "dumb", "COLUMNS": "100"}


class _Asked(BaseModel):
    """The step asked: its name, and its fields' values."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    fields: dict[str, str] = Field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InlineRunner:
    """Runs one step at a time, as `media-hygiene <words>` in a child process."""

    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    program: tuple[str, ...] = (sys.executable, "-m", "media_hygiene")


def inline_step(name: str) -> Step | None:
    """The catalog's step of that name, when the page may run it itself.

    Args:
        name: The step's name.

    Returns:
        It; None for an unknown step or one that is not `inline`.
    """
    found = next((step for step in full_catalog().steps if step.name == name), None)
    return found if found is not None and found.inline else None


async def inline_response(runner: InlineRunner, request: Request) -> Response:
    """Run the step asked and answer its output.

    Args:
        runner: The lock and the program.
        request: `POST /api/inline`, `{"name": …, "fields": {…}}`.

    Returns:
        `{"ok", "output", "command"}`; 404 for a step not run here, 422 for a value
        refused, 409 while another step runs.
    """
    refused = refused_post(request)
    if refused is not None:
        return refused
    try:
        asked = _Asked.model_validate_json(request.body)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    step = inline_step(asked.name)
    if step is None:
        message = _("This step does not run in the page.")
        return json_response(HTTPStatus.NOT_FOUND, {"error": message})
    try:
        words = checked_words(step, asked.fields) if step.fields else step.words({})
    except FieldError as error:
        return json_response(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(error)})
    if runner.lock.locked():
        message = _("Another step runs: wait for its end.")
        return json_response(HTTPStatus.CONFLICT, {"error": message})
    async with runner.lock:
        code, output = await _run(runner.program, words)
    command = f"{LAUNCHER_FUNCTION} {shown(words)}"
    return json_response(
        HTTPStatus.OK, {"ok": code == 0, "output": output, "command": command}
    )


async def _run(program: tuple[str, ...], words: tuple[str, ...]) -> tuple[int, str]:
    """Run the command, its output plain, stopped past the time limit.

    Args:
        program: The command line before the words.
        words: The step's words.

    Returns:
        The exit code and the output, without colours nor traceback.
    """
    process = await asyncio.create_subprocess_exec(
        *program,
        *words,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env={**os.environ, **_PLAIN, "PYTHONIOENCODING": "utf-8"},
    )
    try:
        raw, _unused = await asyncio.wait_for(process.communicate(), INLINE_SECONDS)
    except TimeoutError:
        process.kill()
        await process.wait()
        message = _("Stopped after {seconds} s: run it from the console instead.")
        return 1, message.format(seconds=INLINE_SECONDS)
    return process.returncode or 0, plain(raw.decode("utf-8", errors="replace"))


def plain(text: str) -> str:
    """The output as the page shows it: no colour code, no traceback.

    Args:
        text: What the command wrote.

    Returns:
        It, a traceback replaced by its last line (the error's message).
    """
    text = _ANSI.sub("", text)
    if _TRACEBACK in text:
        before, _sep, after = text.partition(_TRACEBACK)
        last = next((line for line in reversed(after.splitlines()) if line.strip()), "")
        text = f"{before}{last}\n"
    return text.strip()
