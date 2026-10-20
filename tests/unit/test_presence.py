"""A page's server ends once no tab shows it (0261): a tab closed, never a reload.

The delays are shortened here; the real ones are seconds (a reload) and minutes (a tab
in the background, whose timers browsers slow down).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.review import presence as presence_module
from media_hygiene.review.ending import STOPPED, Ending
from media_hygiene.review.http import Request
from media_hygiene.review.presence import Presence, presence_response

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

_GRACE: Final = 0.05
_SILENCE: Final = 0.3
_CODE: Final = 99
_JSON: Final = {"host": "127.0.0.1:8088", "content-type": "application/json"}


@pytest.fixture(autouse=True)
def _short_delays(monkeypatch: pytest.MonkeyPatch) -> None:
    """Delays of a test, not of a user."""
    monkeypatch.setattr(presence_module, "LEAVING_GRACE_SECONDS", _GRACE)
    monkeypatch.setattr(presence_module, "SILENCE_SECONDS", _SILENCE)


def _run[T](scenario: Callable[[Ending, Presence], Coroutine[None, None, T]]) -> T:
    """Run a scenario on a fresh ending and presence; give what it returns."""

    async def main() -> T:
        ending = Ending()
        return await scenario(ending, Presence(ending, _CODE))

    return asyncio.run(main())


def test_nothing_ends_before_a_first_tab_spoke() -> None:
    """A page opened late, or never: still served."""

    async def scenario(ending: Ending, _presence: Presence) -> int | None:
        await asyncio.sleep(_SILENCE + _GRACE)
        return ending.asked

    assert _run(scenario) is None


def test_a_tab_closed_ends_the_server_with_its_code() -> None:
    """The tab left and none came back: ended, and remembered as closed."""

    async def scenario(ending: Ending, presence: Presence) -> tuple[int, bool]:
        presence.seen(leaving=False)
        presence.seen(leaving=True)
        return await asyncio.wait_for(ending.wait(), 1), presence.closed

    assert _run(scenario) == (_CODE, True)


def test_a_reload_does_not_end_it() -> None:
    """Leaving then back at once (a reload): still served past the grace delay."""

    async def scenario(ending: Ending, presence: Presence) -> int | None:
        presence.seen(leaving=True)
        presence.seen(leaving=False)
        await asyncio.sleep(_GRACE * 3)
        return ending.asked

    assert _run(scenario) is None


def test_a_long_silence_ends_it() -> None:
    """No news at all beyond the silence delay (the browser gone): ended."""

    async def scenario(ending: Ending, presence: Presence) -> int:
        presence.seen(leaving=False)
        return await asyncio.wait_for(ending.wait(), 1)

    assert _run(scenario) == _CODE


def test_an_end_asked_first_is_kept() -> None:
    """A step chosen (or Quit) ended it first: its code stays, not 'closed'."""

    async def scenario(ending: Ending, presence: Presence) -> tuple[int, bool]:
        presence.seen(leaving=True)
        ending.end(STOPPED)
        await asyncio.sleep(_GRACE * 3)
        return await ending.wait(), presence.closed

    assert _run(scenario) == (STOPPED, False)


@pytest.mark.parametrize(
    ("body", "headers", "status"),
    [
        (b'{"leaving": true}', _JSON, 200),
        (b"", _JSON, 200),
        (b'{"leaving": "soon"}', _JSON, 400),
        (b'{"leaving": true}', {"host": "127.0.0.1:8088"}, 415),
        (b'{"leaving": true}', {**_JSON, "origin": "http://evil.example"}, 403),
    ],
    ids=["leaving", "alive", "bad-body", "not-json", "other-site"],
)
def test_the_route_answers_only_json_from_the_page(
    body: bytes, headers: dict[str, str], status: int
) -> None:
    """`POST /api/alive`: JSON from the page itself, else refused."""

    async def scenario(_ending: Ending, presence: Presence) -> int:
        request = Request("POST", presence_module.PRESENCE_PATH, headers, body)
        return (await presence_response(presence, request)).status

    assert _run(scenario) == status
