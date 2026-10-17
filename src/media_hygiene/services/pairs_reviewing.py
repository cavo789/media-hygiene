"""`media-hygiene review --pairs`: open the review of the folder pairs, serve it.

Same server, same decisions file as the other reviews: only the page and what it
decides differ. The pairs come the most space freed first, as in the report.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.plan.pairs import folder_pairs
from media_hygiene.review.pairs_app import PAIRS_DECIDE_PATH, PAIRS_FILE_PATH, PairsApp
from media_hygiene.review.pairs_session import PairsSession, PairsSource
from media_hygiene.review.pairs_views import PairsStateBuilder
from media_hygiene.review.place import decisions_place
from media_hygiene.services.policy import keep_policy
from media_hygiene.services.review_file import first_save, resume_decisions
from media_hygiene.services.review_serving import ReviewPage, serve_review_page

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.plan.pairs import FolderPair
    from media_hygiene.services.runtime import Runtime

_PAGE_TEMPLATE: Final = "pairs_review.html.j2"


def audit_pairs(findings: AuditFindings) -> tuple[FolderPair, ...]:
    """The folder pairs of an audit, in the report's order.

    Args:
        findings: The audit just run.

    Returns:
        The pairs, the most space freed first.
    """
    plan = findings.plan
    return folder_pairs(
        plan.decisions, findings.folder_files, delete_copies=plan.delete_copies
    )


def open_pairs_review(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> PairsSession:
    """Start the review of the audit's folder pairs, resuming the decisions file.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file, in the container.

    Returns:
        The session, saved once: decisions about pairs that no longer exist are
        dropped.

    Raises:
        DecisionsError: The file is not a decisions file, was made on other
            folders, or cannot be written.
    """
    mapper = runtime.mapper
    builder = PairsStateBuilder(mapper, keep_policy(runtime.settings, mapper))
    place = decisions_place(mapper, runtime.locations.reports_dir, target)
    base = resume_decisions(runtime, findings, target)
    source = PairsSource(audit_pairs(findings), builder, target, place)
    session = PairsSession(source, base)
    first_save(session.save)
    return session


def serve_pairs_review(runtime: Runtime, session: PairsSession, port: int) -> None:
    """Serve the page until Ctrl+C; every decision is saved as it is made.

    Args:
        runtime: Settings, mount points and output.
        session: The review.
        port: The port to listen on, inside the container (0: any free one).
    """
    api = (PAIRS_DECIDE_PATH, PAIRS_FILE_PATH)
    page = ReviewPage(_PAGE_TEMPLATE, session.place, api, partial(PairsApp, session))
    serve_review_page(runtime, page, port)
