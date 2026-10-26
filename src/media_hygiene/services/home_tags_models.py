"""What `tags` run by the home page shows and runs: its phases, figures and halves."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.console.page_progress import PageStep

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.console.page_progress import PageProgress


class TagsPhase(StrEnum):
    """Where `tags` started from the page stands."""

    IDLE = "idle"
    PREPARING = "preparing"  # the cheap words, the count of photos to describe
    ASKING = "asking"  # the page shows the figures and asks
    RUNNING = "running"  # the model describes
    DONE = "done"
    STOPPED = "stopped"
    FAILED = "failed"


class TagFigures(BaseModel):
    """What the page asks with: the console's figures before `Describe them now?`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    files: int
    to_describe: int
    seconds_per_photo: float
    model: str = ""  # empty: no vision model in `[classify.ai]`


class PageTags(BaseModel):
    """What the page shows of `tags`: its steps, its figures, its end."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    phase: TagsPhase = TagsPhase.IDLE
    steps: tuple[PageStep, ...] = ()
    current: str = ""
    figures: TagFigures | None = None
    elapsed: float = 0.0  # seconds since the model started, for the rate
    lines: tuple[str, ...] = ()
    error: str | None = None


@dataclass(frozen=True, slots=True)
class TagsRunner:
    """The two halves of `tags`, reporting to the progress given."""

    prepare: Callable[[PageProgress], TagFigures]
    # The progress, and "stop now?" asked between two photos; returns the end lines.
    describe: Callable[[PageProgress, Callable[[], bool]], tuple[str, ...]]
