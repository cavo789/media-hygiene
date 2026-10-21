"""`media-hygiene review --near`: open the review of near duplicates, serve it.

Same server, same decisions file as the burst review: only the page and what it
decides differ. The groups to check come first on the page; the sure ones follow.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.review.apply_api import ApplyOffer
from media_hygiene.review.near_app import NEAR_DECIDE_PATH, NEAR_FILE_PATH, NearApp
from media_hygiene.review.near_session import NearSession, NearSource
from media_hygiene.review.near_views import NearStateBuilder
from media_hygiene.review.place import decisions_place
from media_hygiene.services.policy import keep_policy
from media_hygiene.services.review_file import first_save, resume_decisions
from media_hygiene.services.review_serving import ReviewPage, serve_review_page

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.review.apply_api import ReviewStart
    from media_hygiene.services.runtime import Runtime

_PAGE_TEMPLATE: Final = "near_review.html.j2"


def open_near_review(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> NearSession:
    """Start the review of the audit's near duplicates, resuming the decisions file.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file, in the container.

    Returns:
        The session, saved once: decisions that changed since are dropped.

    Raises:
        DecisionsError: The file is not a decisions file, was made on other
            folders, or cannot be written.
    """
    mapper = runtime.mapper
    similar = findings.similar
    builder = NearStateBuilder(mapper, keep_policy(runtime.settings, mapper), similar)
    place = decisions_place(mapper, runtime.locations.reports_dir, target)
    base = resume_decisions(runtime, findings, target)
    session = NearSession(NearSource(similar.groups, builder, target, place), base)
    first_save(session.save)
    return session


def serve_near_review(
    runtime: Runtime, session: NearSession, start: ReviewStart
) -> int:
    """Serve the page until Ctrl+C; every decision is saved as it is made.

    Args:
        runtime: Settings, mount points and output.
        session: The review.
        start: The port to listen on, inside the container (0: any free one), and
            the step *Apply now* ends on.

    Returns:
        `100 + n` when *Apply now* chose step `n`; 0 otherwise.
    """
    api = (NEAR_DECIDE_PATH, NEAR_FILE_PATH)
    offer = ApplyOffer(start.apply, lambda: session.decided[0] > 0)
    page = ReviewPage(
        _PAGE_TEMPLATE, session.place, api, partial(NearApp, session), offer
    )
    return serve_review_page(runtime, page, start.port)
