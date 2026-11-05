"""Two more openings of `review_kinds`: the burst series, the intruder files (0594)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.review.app import DECIDE_PATH, FILE_PATH, ReviewApp
from media_hygiene.review.apply_api import ApplyOffer
from media_hygiene.services import reviewing
from media_hygiene.services.albums import album_desk
from media_hygiene.services.aside_paths import review_picker
from media_hygiene.services.intruder_pick import intruders_set_aside
from media_hygiene.services.intruders_reviewing import intruders_page
from media_hygiene.services.review_serving import ReviewPage

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.review.local_app import LocalApp
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

    offer = ApplyOffer(None, lambda: session.progress[1] > 0)
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
