"""More openings of `review_kinds`: the burst series (all, an import's), intruders."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.review.app import DECIDE_PATH, FILE_PATH, ReviewApp
from media_hygiene.review.apply_api import ApplyOffer
from media_hygiene.services import reviewing
from media_hygiene.services.albums import album_desk
from media_hygiene.services.aside_paths import review_picker
from media_hygiene.services.burst_opening import BurstOpening, open_bursts
from media_hygiene.services.import_bursts import import_view
from media_hygiene.services.intruder_pick import intruders_set_aside
from media_hygiene.services.intruders_reviewing import intruders_page
from media_hygiene.services.review_serving import ReviewPage

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.review.local_app import LocalApp
    from media_hygiene.review.session import ReviewSession
    from media_hygiene.services.runtime import Runtime


def bursts(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> ReviewPage | None:
    """`review`: the burst series, their albums too.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file.

    Returns:
        Its page; None without burst series.
    """
    if not findings.similar.bursts:
        return None
    session = reviewing.open_review(runtime, findings, target)
    return _page(runtime, session, ApplyOffer(None, lambda: session.progress[1] > 0))


def imported_bursts(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> ReviewPage | None:
    """The burst series of the last import's new files only (0630).

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file: the library's other series kept in it.

    Returns:
        Its page; every series without a chain; None without a series.
    """
    view = import_view(runtime, findings)
    if view is None:
        return bursts(runtime, findings, target)
    shown, hidden = view
    if not shown.similar.bursts:
        return None
    session = open_bursts(runtime, BurstOpening(shown, target, hidden))
    return _page(runtime, session, ApplyOffer(None, lambda: session.progress[1] > 0))


def _page(runtime: Runtime, session: ReviewSession, offer: ApplyOffer) -> ReviewPage:
    """The page of a burst review, its albums too.

    Args:
        runtime: Settings, mount points and output.
        session: The review.
        offer: Its *Apply now*.

    Returns:
        Its page.
    """
    albums = album_desk(runtime, review_picker(runtime, session))

    def app(page: bytes, executor: Executor, previews: Path | None) -> LocalApp:
        """The burst review's app, with its albums.

        Args:
            page: The page.
            executor: The worker pool.
            previews: The previews' cache folder.

        Returns:
            The app.
        """
        return ReviewApp(session, page, executor, previews, albums)

    api = (DECIDE_PATH, FILE_PATH)
    return ReviewPage(reviewing.PAGE_TEMPLATE, session.place, api, app, offer)


def intruders(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> ReviewPage | None:
    """`review --intruders`: walked again at each request, written to the reports'.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file (unused: the page writes the reports folder's).

    Returns:
        Its page; None without intruder files.
    """
    del target
    if not findings.intruders:
        return None
    offer = ApplyOffer(None, lambda: bool(intruders_set_aside(runtime)))
    return intruders_page(runtime, offer)
