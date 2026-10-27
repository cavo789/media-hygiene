"""`media-hygiene review --intruders`: pick the intruder files to set aside (0428).

The page lists them per extension and per folder, with checkboxes; what is ticked
goes to the `chosen` key of the reports folder's decisions file (`intruder_pick`),
then `clean --decisions` moves it to the quarantine, journaled, `undo`-able.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.intruders_app import INTRUDERS_PATH, IntrudersApp
from media_hygiene.review.intruders_views import intruders_state
from media_hygiene.review.place import DEFAULT_DECISIONS, decisions_place
from media_hygiene.services.intruder_pick import (
    IntruderPick,
    current_intruders,
    intruders_set_aside,
    put_intruders_back,
    set_intruders_aside,
)
from media_hygiene.services.review_serving import ReviewPage, serve_review_page

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.report.chosen_decisions import ChosenFile
    from media_hygiene.review.intruders_app import IntrudersPick
    from media_hygiene.review.intruders_views import IntrudersState
    from media_hygiene.review.local_app import LocalApp
    from media_hygiene.review.place import DecisionsPlace
    from media_hygiene.services.runtime import Runtime

_PAGE_TEMPLATE: Final = "intruders_review.html.j2"


def intruders_place(runtime: Runtime) -> DecisionsPlace:
    """The decisions file the picks go to: the reports folder's.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Its place.
    """
    reports = runtime.locations.reports_dir
    return decisions_place(runtime.mapper, reports, reports / DEFAULT_DECISIONS)


@dataclass(frozen=True, slots=True)
class IntrudersDeskOnDisk:
    """The intruder files of the photo folders, walked again at each request."""

    runtime: Runtime

    def state(self) -> IntrudersState:
        """Describe the intruder files now, and those set aside.

        Returns:
            The state.
        """
        runtime = self.runtime
        where = (runtime.mapper, intruders_place(runtime).host)
        found = current_intruders(runtime)
        return intruders_state(found, intruders_set_aside(runtime), where)

    def pick(self, pick: IntrudersPick) -> tuple[ChosenFile, ...]:
        """Save the extensions and folders ticked (or put all back), then read back.

        Args:
            pick: What the page posted.

        Returns:
            The intruder files set aside, as read back from the disk.
        """
        runtime = self.runtime
        if pick.back:
            put_intruders_back(runtime)
        else:
            folders = tuple(runtime.mapper.to_container(f) for f in pick.folders)
            extensions = frozenset(ext.casefold() for ext in pick.extensions)
            set_intruders_aside(runtime, IntruderPick(extensions, folders))
        return intruders_set_aside(runtime)


def serve_intruders_review(runtime: Runtime, port: int) -> int:
    """Serve the page until Ctrl+C; every pick is saved as it is made.

    Args:
        runtime: Settings, mount points and output.
        port: The port to listen on, inside the container (0: any free one).

    Returns:
        As `serve_review_page`.
    """
    desk = IntrudersDeskOnDisk(runtime)

    def app(page: bytes, _executor: Executor, _previews: Path | None) -> LocalApp:
        """Build the app answering the browser.

        Args:
            page: The page (no preview: the pool and the cache are unused).

        Returns:
            The app.
        """
        return IntrudersApp(desk, page)

    api = (INTRUDERS_PATH, FILE_PATH)
    page = ReviewPage(_PAGE_TEMPLATE, intruders_place(runtime), api, app)
    return serve_review_page(runtime, page, port)
