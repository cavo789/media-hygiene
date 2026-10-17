"""`review --gone` in the terminal: what is to answer, then what comes next (0224)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.review_next import CleanNext, tell_choices_and_clean
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.services import gone_reviewing

if TYPE_CHECKING:
    from media_hygiene.cli.review_modes import ReviewRun
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.review.gone_session import GoneSession
    from media_hygiene.services.runtime import Runtime


def run_gone(run: ReviewRun, findings: AuditFindings) -> None:
    """`review --gone`: the files gone since an audit, folder by folder.

    Args:
        run: The command line, runtime, decisions file and port.
        findings: The audit just run (it recorded the files gone).
    """
    runtime = run.runtime
    if not gone_reviewing.files_gone(runtime):
        runtime.output.success(
            _("No photo nor video has disappeared: nothing to review.")
        )
        return
    session = gone_reviewing.open_gone_review(runtime, findings, run.target)
    tell_gone_opened(runtime, session)
    gone_reviewing.serve_gone_review(runtime, session, run.port)
    _tell_gone_stopped(run, session)


def tell_gone_opened(runtime: Runtime, session: GoneSession) -> None:
    """Say how many files are gone, and what changed since the last review.

    Args:
        runtime: Settings, mount points and output.
        session: The review, opened.
    """
    output = runtime.output
    _decided, _deleted, total = session.decided
    message = ngettext(
        "{count} photo or video has disappeared since an audit: deleted on purpose, "
        "or moved to a disk not plugged in? Only you can tell.",
        "{count} photos and videos have disappeared since an audit: deleted on "
        "purpose, or moved to a disk not plugged in? Only you can tell.",
        total,
    )
    output.info(message.format(count=human_number(total)))
    if session.dropped:
        dropped = ngettext(
            "{count} file answered earlier is no longer recorded as gone: its answer "
            "is dropped.",
            "{count} files answered earlier are no longer recorded as gone: their "
            "answers are dropped.",
            session.dropped,
        )
        output.warning(dropped.format(count=human_number(session.dropped)))


def _tell_gone_stopped(run: ReviewRun, session: GoneSession) -> None:
    """Sum the review up once stopped, and say what comes next.

    Args:
        run: The command line, runtime, decisions file and port.
        session: The review, stopped.
    """
    output = run.runtime.output
    decided, deleted, total = session.decided
    output.blank()
    output.success(
        _(
            "Review stopped — files answered: {decided} of {total}, deleted on "
            "purpose: {deleted}."
        ).format(
            decided=human_number(decided),
            total=human_number(total),
            deleted=human_number(deleted),
        )
    )
    if not decided:
        output.info(_("Your choices are in {place}.").format(place=session.place.host))
        return
    text = _(
        "the same 'clean' command with {option}; the files deleted on purpose are "
        "remembered, nothing moves, 'undo' forgets them."
    )
    tell_choices_and_clean(run.ctx, run.runtime, CleanNext(session.place, text))
