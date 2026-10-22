"""The show the server holds (0291): next, previous, jump, "do not show", the timer.

`Show` with a clock the test moves; `Desk` answering the phone's actions and waking
the pages waiting for a change.
"""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import Final

import pytest

from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.screens import Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Slide, Timing

_INTERVAL: Final = 8.0


class _Clock:
    """A clock the test moves by hand."""

    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


def _show(count: int = 4, clock: _Clock | None = None) -> Show:
    slides = tuple(Slide(key, f"2026-07-0{key}") for key in range(1, count + 1))
    return Show(slides, Timing(_INTERVAL, clock or _Clock()))


def _shown(show: Show) -> int | None:
    return None if show.current is None else show.current.key


def _keys(show: Show, moves: int) -> list[int | None]:
    seen = []
    for _move in range(moves):
        show.move(1)
        seen.append(None if show.current is None else show.current.key)
    return seen


def test_next_and_previous_go_round_the_selection() -> None:
    """After the last, the first; before the first, the last; each move a version."""
    show = _show()
    assert show.current == Slide(1, "2026-07-01")
    assert show.upcoming == Slide(2, "2026-07-02")
    assert _keys(show, 4) == [2, 3, 4, 1]
    before = show.version
    show.move(-1)
    assert show.current is not None
    assert show.current.key == 4
    assert show.version == before + 1


def test_a_photo_set_out_is_passed_over_and_a_jump_brings_it_back() -> None:
    """Out: next skips it, the TV moves on when it showed it; a jump shows it again."""
    show = _show()
    assert show.set_out(2, out=True)
    assert _keys(show, 3) == [3, 4, 1]
    assert show.set_out(1, out=True)  # shown now: the TV moves on
    assert show.current is not None
    assert show.current.key == 3
    assert show.skipped == {1, 2}
    assert show.jump(2)
    assert show.current is not None
    assert show.current.key == 2
    assert show.skipped == {1}
    assert not show.jump(99)
    assert not show.set_out(99, out=True)


def test_every_photo_set_out_shows_nothing_until_one_comes_back() -> None:
    """Nothing on the TV, no next one; a photo set back in is shown at once."""
    show = _show(2)
    show.set_out(1, out=True)
    show.set_out(2, out=True)
    assert show.current is None
    assert show.upcoming is None
    show.move(1)
    assert show.current is None
    show.set_out(2, out=False)
    assert _shown(show) == 2
    assert show.upcoming is None  # the only one left


def test_an_empty_selection_never_fails() -> None:
    """No photo: nothing shown, moving does nothing."""
    show = Show((), Timing(_INTERVAL))
    show.move(1)
    show.move(-1)
    assert show.current is None
    assert show.position is None


def test_the_timer_moves_on_once_the_interval_is_over() -> None:
    """Paused: never; playing: after the interval, counted again from each move."""
    clock = _Clock()
    show = _show(clock=clock)
    clock.now += 100
    assert show.wait_seconds() is None
    assert not show.tick()
    show.play(playing=True)
    assert show.wait_seconds() == _INTERVAL
    clock.now += _INTERVAL - 1
    assert not show.tick()
    show.move(1)  # a choice on the phone: the interval starts again
    clock.now += _INTERVAL - 1
    assert not show.tick()
    clock.now += 1
    assert show.tick()
    assert show.current is not None
    assert show.current.key == 3


def _desk(show: Show) -> Desk:
    return Desk(show, Screens(), Changes())


def _ask(desk: Desk, value: object) -> tuple[HTTPStatus, dict[str, object]]:
    response = desk.ask(json.dumps(value).encode())
    body = json.loads(response.body) if response.body else {}
    return response.status, body


def test_the_phone_s_actions_change_the_show() -> None:
    """Each action answers the show as it now is; a bad one changes nothing."""
    desk = _desk(_show())
    status, state = _ask(desk, {"action": "next"})
    assert status is HTTPStatus.OK
    assert state["current"] == 2
    assert state["place"] == 2
    assert state["total"] == 4
    assert _ask(desk, {"action": "previous"})[1]["current"] == 1
    assert _ask(desk, {"action": "jump", "key": 4})[1]["current"] == 4
    assert _ask(desk, {"action": "out", "key": 2})[1]["out"] == [2]
    assert _ask(desk, {"action": "in", "key": 2})[1]["out"] == []
    playing = _ask(desk, {"action": "play"})[1]
    assert playing["playing"] is True
    assert playing["seconds"] == _INTERVAL
    assert _ask(desk, {"action": "pace", "seconds": 15})[1]["seconds"] == 15
    assert _ask(desk, {"action": "pause"})[1]["playing"] is False
    assert _ask(desk, {"action": "jump", "key": 99})[0] is HTTPStatus.NOT_FOUND
    assert _ask(desk, {"action": "pace", "seconds": 1})[0] is HTTPStatus.BAD_REQUEST
    assert _ask(desk, {"action": "explode"})[0] is HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize("since_seen", [True, False])
def test_a_page_waits_for_a_change_it_has_not_seen(*, since_seen: bool) -> None:
    """A version seen waits for the next change; an older one answers at once."""
    desk = _desk(_show())

    async def scenario() -> int:
        since = desk.show.version if since_seen else 0
        waiting = asyncio.create_task(desk.settle(since, limit=5.0))
        await asyncio.sleep(0)
        assert waiting.done() is not since_seen
        desk.ask(b'{"action": "next"}')
        await asyncio.wait_for(waiting, 1.0)
        return desk.show.version

    assert asyncio.run(scenario()) > 1


def test_a_page_waiting_moves_the_show_on_when_it_plays() -> None:
    """The timer is read by whoever waits: a playing show moves without any choice."""
    desk = Desk(Show((Slide(1), Slide(2)), Timing(0.01)), Screens(), Changes())
    desk.show.play(playing=True)
    seen = desk.show.version
    asyncio.run(desk.settle(seen, limit=2.0))
    assert desk.show.version > seen
    assert desk.show.current == Slide(2)


def test_a_page_waiting_too_long_gets_the_show_unchanged() -> None:
    """The long poll ends after its limit, the version unchanged."""
    desk = _desk(_show())
    seen = desk.show.version
    asyncio.run(desk.settle(seen, limit=0.01))
    assert desk.show.version == seen
