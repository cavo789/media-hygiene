"""The short steps the home server runs itself, their output in a dialog (0505)."""

from __future__ import annotations

import asyncio
import json
import sys
from http import HTTPStatus
from typing import Final

from media_hygiene.cli.menu_steps import full_catalog
from media_hygiene.review.home_tags_api import INLINE_PATH
from media_hygiene.review.http import Request
from media_hygiene.review.inline_step import (
    InlineRunner,
    inline_response,
    inline_step,
    plain,
)
from media_hygiene.review.write_routes import CHANGES
from media_hygiene.services.home import home_page

_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}
_INLINE: Final = frozenset({"config", "backup", "history", "reports-prune"})
# Writes its words in colour, so that the test sees what the page receives.
_ECHO: Final = "import sys; print('\\x1b[1mran\\x1b[0m', *sys.argv[1:])"
_CRASH: Final = "raise ValueError('index locked')"


def _runner(script: str) -> InlineRunner:
    """A runner whose program is a small script instead of media-hygiene."""
    return InlineRunner(program=(sys.executable, "-c", script))


def _ask(runner: InlineRunner, body: object) -> tuple[HTTPStatus, dict[str, object]]:
    """Send the request as the page does."""
    request = Request("POST", INLINE_PATH, _JSON, json.dumps(body).encode())
    reply = asyncio.run(inline_response(runner, request))
    return reply.status, json.loads(reply.body or b"{}")


def test_the_catalog_flags_the_short_steps_only() -> None:
    """The four candidates without a prompt; no step that asks or lasts."""
    flagged = {step.name for step in full_catalog().steps if step.inline}
    assert flagged == _INLINE
    assert inline_step("clean") is None
    assert inline_step("nope") is None


def test_a_step_runs_and_its_output_comes_back_plain() -> None:
    """Its words given, the colours removed, the command named."""
    status, answer = _ask(_runner(_ECHO), {"name": "history"})
    assert status == HTTPStatus.OK
    assert answer["ok"] is True
    assert answer["output"] == "ran history"
    assert str(answer["command"]).endswith("history")


def test_a_field_is_checked_then_given() -> None:
    """`reports --prune {count}`: a number runs, a word is refused."""
    runner = _runner(_ECHO)
    status, answer = _ask(runner, {"name": "reports-prune", "fields": {"count": "5"}})
    assert status == HTTPStatus.OK
    assert answer["output"] == "ran reports --prune 5"
    status, answer = _ask(runner, {"name": "reports-prune", "fields": {"count": "x"}})
    assert status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert answer["error"]


def test_a_step_not_run_here_is_refused() -> None:
    """`clean` asks in the console: never run by the page."""
    status, _answer = _ask(_runner(_ECHO), {"name": "clean"})
    assert status == HTTPStatus.NOT_FOUND


def test_an_error_shows_its_message_never_a_traceback() -> None:
    """The child crashed: the page reads the last line only."""
    status, answer = _ask(_runner(_CRASH), {"name": "config"})
    assert status == HTTPStatus.OK
    assert answer["ok"] is False
    assert answer["output"] == "ValueError: index locked"
    assert plain("x\nTraceback (most recent call last):\n  f\nE: m\n") == "x\nE: m"


def test_a_second_step_while_one_runs_is_refused() -> None:
    """One at a time: 409, said."""
    runner = _runner(_ECHO)

    async def both() -> HTTPStatus:
        async with runner.lock:
            request = Request(
                "POST", INLINE_PATH, _JSON, json.dumps({"name": "config"}).encode()
            )
            return (await inline_response(runner, request)).status

    assert asyncio.run(both()) == HTTPStatus.CONFLICT


def test_the_page_knows_the_path_and_a_phone_may_not_post_it() -> None:
    """The page posts to it; the phone's read-only door refuses it."""
    assert INLINE_PATH.encode() in home_page()
    assert INLINE_PATH in CHANGES
