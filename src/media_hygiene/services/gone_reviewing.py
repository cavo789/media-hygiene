"""`media-hygiene review --gone`: the files gone since an audit, answered one by one.

Same server, same decisions file as the other reviews. Nothing is remembered until
the user says a file was deleted on purpose; `clean --decisions` then writes the
journal marks (0224).
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.index.gone_rows import gone_records
from media_hygiene.index.repository import FactsRepository
from media_hygiene.review.gone_app import GONE_DECIDE_PATH, GONE_FILE_PATH, GoneApp
from media_hygiene.review.gone_session import GonePages, GoneSession
from media_hygiene.review.gone_views import GoneStateBuilder, ordered
from media_hygiene.review.place import decisions_place
from media_hygiene.services.review_file import first_save, resume_decisions
from media_hygiene.services.review_serving import ReviewPage, serve_review_page

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.index.gone_rows import GoneRecord
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime

_PAGE_TEMPLATE: Final = "gone_review.html.j2"


def files_gone(runtime: Runtime) -> tuple[GoneRecord, ...]:
    """The files gone waiting for an answer, by folder and day.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Them; none without a persistent index.
    """
    if runtime.index_file is None or not runtime.index_file.is_file():
        return ()
    with FactsRepository.open(runtime.index_file) as repository:
        return ordered(gone_records(repository.connection))


def open_gone_review(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> GoneSession:
    """Start the review of the files gone, resuming the file.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run (it recorded the files gone).
        target: The decisions file, in the container.

    Returns:
        The session, saved once: answers about files no longer recorded are dropped.

    Raises:
        DecisionsError: The file is not a decisions file, was made on other
            folders, or cannot be written.
    """
    mapper = runtime.mapper
    builder = GoneStateBuilder(mapper, runtime.previews_dir)
    place = decisions_place(mapper, runtime.locations.reports_dir, target)
    base = resume_decisions(runtime, findings, target)
    session = GoneSession(GonePages(files_gone(runtime), builder, target, place), base)
    first_save(session.save)
    return session


def serve_gone_review(runtime: Runtime, session: GoneSession, port: int) -> None:
    """Serve the page until Ctrl+C; every answer is saved as it is made.

    Args:
        runtime: Settings, mount points and output.
        session: The review.
        port: The port to listen on, inside the container (0: any free one).
    """
    api = (GONE_DECIDE_PATH, GONE_FILE_PATH)
    page = ReviewPage(_PAGE_TEMPLATE, session.place, api, partial(GoneApp, session))
    serve_review_page(runtime, page, port)
