"""`media-hygiene review --near`: open the review of near duplicates, serve it.

Same server, same decisions file as the burst review: only the page and what it
decides differ. The groups to check come first on the page; the sure ones follow.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.review.near_app import NEAR_DECIDE_PATH, NEAR_FILE_PATH, NearApp
from media_hygiene.review.near_session import NearSession, NearSource
from media_hygiene.review.near_views import NearStateBuilder
from media_hygiene.review.place import decisions_place
from media_hygiene.services.policy import keep_policy
from media_hygiene.services.review_file import (
    first_save,
    resume_decisions,
    review_page,
)
from media_hygiene.services.reviewing import address_tip, page_url, run_server

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings
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


def serve_near_review(runtime: Runtime, session: NearSession, port: int) -> None:
    """Serve the page until Ctrl+C; every decision is saved as it is made.

    Args:
        runtime: Settings, mount points and output.
        session: The review.
        port: The port to listen on, inside the container (0: any free one).
    """
    api = (NEAR_DECIDE_PATH, NEAR_FILE_PATH)
    page = review_page(_PAGE_TEMPLATE, session.place, api)

    def ready(port: int) -> None:
        """Tell where the page is and how to open it from the host.

        Args:
            port: The port listened on, inside the container.
        """
        runtime.output.success(
            _(
                "Review ready, open {url} in your browser. Each decision is saved "
                "at once in {place}. Ctrl+C stops the review."
            ).format(url=page_url(port), place=session.place.host)
        )
        address_tip(runtime.output, port)

    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = NearApp(session, page, executor, runtime.previews_dir)
        asyncio.run(run_server(app, port, ready))
