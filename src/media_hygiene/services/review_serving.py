"""Serve one review page until Ctrl+C: `review --near`, `--pairs`, `--junk`.

Each one only says which page it renders, the routes it calls, and the app answering
the browser; the server, the address told and the stop are the same, *Apply now* too
when the page offers it (0288).
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.person.door import with_person
from media_hygiene.review.apply_api import ApplyOffer, applying_door
from media_hygiene.review.ending import serve_until_ended
from media_hygiene.services.review_file import review_page
from media_hygiene.services.reviewing import address_tip, page_url

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.review.local_app import LocalApp
    from media_hygiene.review.place import DecisionsPlace
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class ReviewPage:
    """A review page: its template, its decisions file, its routes, its app."""

    template: str
    place: DecisionsPlace
    api: tuple[str, str]  # the path that decides, the path that reads the file back
    # The app, from the page, the worker pool and the previews' cache folder.
    app: Callable[[bytes, Executor, Path | None], LocalApp]
    # Opened from the home page, the step *Apply now* ends on (None: no button).
    apply: ApplyOffer | None = None


def serve_review_page(runtime: Runtime, review: ReviewPage, port: int) -> int:
    """Serve the page until Ctrl+C; every decision is saved as it is made.

    Args:
        runtime: Settings, mount points and output.
        review: The page and its app.
        port: The port to listen on, inside the container (0: any free one).

    Returns:
        `STEP_EXIT_BASE + n` when *Apply now* chose step `n`; 0 otherwise.
    """
    page = review_page(review.template, review.place, review.api)

    def ready(port: int) -> None:
        """Tell where the page is and how to open it from the host.

        Args:
            port: The port listened on, inside the container.
        """
        runtime.output.success(
            _(
                "Review ready, open {url} in your browser. Each decision is saved "
                "at once in {place}. Ctrl+C stops the review."
            ).format(url=page_url(port), place=review.place.host)
        )
        address_tip(runtime.output, port)

    offer = review.apply or ApplyOffer(None, _nothing)
    code = 0
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        door = applying_door(review.app(page, executor, runtime.previews_dir), offer)
        door = with_person(door, runtime, executor)
        code = asyncio.run(serve_until_ended(door, port, ready))
    return code


def _nothing() -> bool:
    """A page without *Apply now*: nothing it could apply.

    Returns:
        False.
    """
    return False
