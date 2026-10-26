"""The pages of `search` and `browse`, one server of their own.

The app itself (`search_app`) is the one the home server serves too (0356). This server
runs until Ctrl+C, or until *Apply now* (`browse` opened from the home page) ends it on
the step that applies the decisions.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.constants import ExitCode
from media_hygiene.person.door import with_person
from media_hygiene.review.ending import Ending, EndingDoor, serve_until_ended
from media_hygiene.review.presence import Presence
from media_hygiene.services.reviewing import address_tip, page_url
from media_hygiene.services.search_app import SearchBuild, search_app

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.apply_api import ApplyStep
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class PageStart:
    """The port, the page `/` serves (`/search` or `/browse`), and how it is said."""

    port: int
    path: str
    ready: str  # translated, with `{url}`
    # Opened from the home page: the step *Apply now* ends on (None: no button).
    apply: Callable[[], ApplyStep | None] | None = None
    query: str = ""  # added to the address said: `?folder=…` opens on a folder (0405)


@dataclass(frozen=True, slots=True)
class Served:
    """How the pages ended: what is set aside, and the exit code asked for."""

    chosen: int  # read from the disk
    code: int = 0  # `STEP_EXIT_BASE + n`: *Apply now* chose step `n`


def serve_pages(runtime: Runtime, search: SearchIndex, start: PageStart) -> Served:
    """Serve the search and the folder view until Ctrl+C or *Apply now*.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        start: The port and the page to announce.

    Returns:
        How many files are set aside when the pages stop, read from the disk, and
        the exit code a page asked for.
    """
    ending = Ending()
    code = 0
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = search_app(
            runtime, search, SearchBuild(start.path, start.apply, ending, executor)
        )
        closing = Presence(ending, ExitCode.PAGE_CLOSED)  # its tab closed (0262)
        door = EndingDoor(app, ending, closing)
        door = with_person(door, runtime, executor)
        ready = partial(_announce, runtime, start)
        code = asyncio.run(serve_until_ended(door, start.port, ready))
    return Served(len(app.place.chosen.paths()), code)


def _announce(runtime: Runtime, start: PageStart, port: int) -> None:
    """Tell where the page is and how to open it from the host.

    Args:
        runtime: Settings, mount points and output.
        start: The page announced, and how.
        port: The port listened on, inside the container.
    """
    runtime.output.success(start.ready.format(url=page_url(port) + start.query))
    address_tip(runtime.output, port)
