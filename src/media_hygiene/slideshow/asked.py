"""What a remote asks of the show (`POST /api/show`): an action and what it names."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.config.slideshow_settings import LONGEST_INTERVAL, SHORTEST_INTERVAL
from media_hygiene.slideshow.chapters import Telling


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
    STOP = "stop"  # end the show: the TV says so, the remote offers another (0633)
    UNTICK = "untick"  # set out every photo of the event `folder` (0832)
    TICK = "tick"  # back in what unticking the event `folder` had set out (0832)


class ShowAsked(BaseModel):
    """`POST /api/show`: an action, the photo it names, the interval it sets."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Action
    key: int | None = None
    seconds: int | None = Field(default=None, ge=SHORTEST_INTERVAL, le=LONGEST_INTERVAL)
    where: Telling | None = None
    folder: str | None = None  # an event's folder: its key (0832)
