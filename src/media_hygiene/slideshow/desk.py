"""The show as the pages see it: what they wait for, what the phone asks.

The TV and the phone each ask "what now?" with the version they last saw; the answer
waits (a long poll, `WAIT_SECONDS` at most) until the show changes: a choice on a
phone, the timer moving on. Whoever waits reads the timer (`Show.tick`), so a show
plays as long as a page looks at it.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from enum import StrEnum
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.slideshow_settings import LONGEST_INTERVAL, SHORTEST_INTERVAL
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.slideshow.chapters import Telling
from media_hygiene.slideshow.notes import event_start, story_view
from media_hygiene.slideshow.slides import Timing

if TYPE_CHECKING:
    from media_hygiene.slideshow.screens import Screens
    from media_hygiene.slideshow.show import Show

# Under the 30 s a browser or a proxy commonly waits for an answer.
WAIT_SECONDS: Final = 25.0


class Action(StrEnum):
    """What the phone asks of the show."""

    NEXT = "next"
    PREVIOUS = "previous"
    JUMP = "jump"  # show the photo `key`
    OUT = "out"  # do not show the photo `key`
    IN = "in"  # show the photo `key` again in its turn
    PLAY = "play"
    PAUSE = "pause"
    PACE = "pace"  # each photo stays `seconds`
    TELL = "tell"  # tell the events `where` (0448)
    EVENT = "event"  # back to the start of this event (0449)
    NEXT_EVENT = "next_event"  # the first photo of the next event (0449)


class ShowAsked(BaseModel):
    """`POST /api/show`: an action, the photo it names, the interval it sets."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Action
    key: int | None = None
    seconds: int | None = Field(default=None, ge=SHORTEST_INTERVAL, le=LONGEST_INTERVAL)
    where: Telling | None = None


class Changes:
    """Wakes the pages waiting once the show changed."""

    __slots__ = ("_event",)

    def __init__(self) -> None:
        """Start with nobody woken."""
        self._event = asyncio.Event()

    def notify(self) -> None:
        """Wake every page waiting now; the next ones wait for the next change."""
        self._event.set()
        self._event = asyncio.Event()

    async def wait(self, seconds: float) -> None:
        """Wait for a change, at most a while.

        Args:
            seconds: The longest wait.
        """
        event = self._event
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(event.wait(), seconds)


@dataclass(frozen=True, slots=True)
class Desk:
    """The show, the TVs paired, and the pages waiting for a change."""

    show: Show
    screens: Screens
    changes: Changes

    async def settle(self, since: int, limit: float = WAIT_SECONDS) -> None:
        """Wait until the show is no longer at a version, or a while passed.

        Args:
            since: The version the page saw.
            limit: The longest wait, in seconds.
        """
        loop = asyncio.get_running_loop()
        end = loop.time() + limit
        while self.show.version == since:
            if self.show.tick():
                self.changes.notify()
                return
            left = end - loop.time()
            if left <= 0:
                return
            timer = self.show.wait_seconds()
            await self.changes.wait(left if timer is None else min(left, timer))

    def state(self) -> dict[str, object]:
        """The show for the phone.

        Returns:
            The version, the photo shown (its key, its place from 1), whether it
            plays, the interval, the photos set out, the TVs paired, whether the
            videos are shown, whether a TV waits for its code.
        """
        show = self.show
        current = show.current
        chapter = None if current is None else current.chapter
        return {
            "version": show.version,
            "current": None if current is None else current.key,
            "place": None if show.position is None else show.position + 1,
            "total": len(show.slides),
            "playing": show.playing,
            "seconds": round(show.timing.interval),
            "out": sorted(show.skipped),
            "screens": self.screens.paired,
            "tvWaiting": self.screens.waiting,  # the code field on top (0456)
            "films": show.films,  # False: every TV shows photos only (0292)
            "telling": self.screens.telling.value,
            "chapter": None if chapter is None else chapter.view(),
            "story": story_view(show),
        }

    def ask(self, body: bytes) -> Response:
        """Apply what the phone asked.

        Args:
            body: The JSON the page sent.

        Returns:
            The show as it now is; 400 for a body that is not an action, 404 for a
            photo not in the show.
        """
        try:
            asked = ShowAsked.model_validate_json(body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        if not self._apply(asked):
            return Response(HTTPStatus.NOT_FOUND)
        self.changes.notify()
        return json_response(HTTPStatus.OK, self.state())

    def _apply(self, asked: ShowAsked) -> bool:
        """Change the show as the phone asked.

        Args:
            asked: The action, its photo, its interval.

        Returns:
            False for a photo not in the show.
        """
        show = self.show
        key = -1 if asked.key is None else asked.key
        match asked.action:
            case Action.NEXT | Action.PREVIOUS:
                show.move(1 if asked.action is Action.NEXT else -1)
            case Action.PLAY | Action.PAUSE:
                show.play(playing=asked.action is Action.PLAY)
            case Action.PACE:
                seconds = asked.seconds or show.timing.interval
                show.timing = Timing(seconds, show.timing.clock)
                show.play(playing=show.playing)
            case Action.TELL:
                self.screens.telling = asked.where or Telling.TV
                show.version += 1
            case Action.JUMP:
                return show.jump(key)
            case Action.EVENT | Action.NEXT_EVENT:
                start = event_start(show, int(asked.action is Action.NEXT_EVENT))
                return start is None or show.jump(start)  # no next event: stays
            case Action.OUT | Action.IN:
                return show.set_out(key, out=asked.action is Action.OUT)
        return True
