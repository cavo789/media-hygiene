"""`media-hygiene review`: open the burst series review and serve it until Ctrl+C.

The server listens on every interface of the container: Docker publishes the port on
the host's loopback only, under the same number (`-p 127.0.0.1:8088:8088`): the page's
address on the host is then known and printed as is.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.app import DECIDE_PATH, FILE_PATH, ReviewApp
from media_hygiene.review.place import decisions_place
from media_hygiene.review.session import ReviewSession, ReviewSource
from media_hygiene.review.views import StateBuilder
from media_hygiene.services.missing_mount import missing_mount, typed_again
from media_hygiene.services.next_command import LAUNCHER_VARIABLE, NextVerb
from media_hygiene.services.policy import keep_policy, proposal_limits
from media_hygiene.services.review import decisions_path
from media_hygiene.services.review_file import (
    first_save,
    resume_decisions,
    review_page,
)
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.console.output import Output
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.review.serving import Connected
    from media_hygiene.services.runtime import Runtime

# Every interface of the container: Docker forwards the published port to it.
LISTEN_HOST: Final = "0.0.0.0"  # noqa: S104
HOST_LOOPBACK: Final = "127.0.0.1"
_PAGE_TEMPLATE: Final = "review.html.j2"


def review_target(runtime: Runtime, decisions: Path, port: int) -> Path:
    """Check, before the audit, that the decisions file will outlive the container.

    Args:
        runtime: Settings, mount points and output.
        decisions: `--decisions` value; a relative path lies in the reports folder.
        port: The port of the page, published again by the command offered.

    Returns:
        The decisions file, in the container.

    Raises:
        MountError: The reports folder is not mounted, or not writable.
    """
    if not decisions.is_absolute():
        if not runtime.persistent(MountKind.REPORTS):
            again = NextVerb(typed_again(runtime, "review"), (MountKind.REPORTS,), port)
            raise missing_mount(
                runtime,
                _("The decisions are saved in /reports: mount it, or they are lost."),
                again,
            )
        ensure_writable(runtime, MountKind.REPORTS)
    return decisions_path(runtime, decisions)


def open_review(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> ReviewSession:
    """Start the review of the audit's burst series, resuming the decisions file.

    The file is written at once, every series listed: `todo` until seen.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file, in the container.

    Returns:
        The session.

    Raises:
        DecisionsError: The file is not a decisions file, was made on other
            folders, or cannot be written.
    """
    mapper = runtime.mapper
    builder = StateBuilder(
        mapper,
        keep_policy(runtime.settings, mapper),
        findings.similar,
        proposal_limits(runtime.settings.review),
    )
    place = decisions_place(mapper, runtime.locations.reports_dir, target)
    source = ReviewSource(findings.similar.bursts, builder, target, place)
    session = ReviewSession(source, resume_decisions(runtime, findings, target))
    first_save(session.save)
    return session


def serve_review(runtime: Runtime, session: ReviewSession, port: int) -> None:
    """Serve the review page until Ctrl+C; every decision is saved as it is made.

    Args:
        runtime: Settings, mount points and output.
        session: The review.
        port: The port to listen on, inside the container (0: any free one).
    """
    page = review_page(_PAGE_TEMPLATE, session.place, (DECIDE_PATH, FILE_PATH))
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = ReviewApp(session, page, executor, runtime.previews_dir)
        asyncio.run(run_server(app, port, partial(_announce, runtime, session)))


async def run_server(app: Connected, port: int, ready: Callable[[int], None]) -> None:
    """Listen, tell the port, and serve until cancelled.

    Args:
        app: Answers each connection.
        port: The port to listen on (0: any free one).
        ready: Called with the port actually listened on.
    """
    server = await asyncio.start_server(app.connection, LISTEN_HOST, port)
    async with server:
        ready(server.sockets[0].getsockname()[1])
        await server.serve_forever()


def _announce(runtime: Runtime, session: ReviewSession, port: int) -> None:
    """Tell where the review is and how to open it from the host.

    Args:
        runtime: Settings, mount points and output.
        session: The review.
        port: The port listened on, inside the container.
    """
    output = runtime.output
    output.success(
        _(
            "Review ready, open {url} in your browser. Each decision is saved at "
            "once in {place}. Ctrl+C stops the review."
        ).format(url=page_url(port), place=session.place.host)
    )
    address_tip(output, port)


def page_url(port: int) -> str:
    """The page's address on the host, published under the same port number.

    Args:
        port: The port listened on, inside the container.

    Returns:
        The URL to open in the browser.
    """
    return f"http://{HOST_LOOPBACK}:{port}/"


def address_tip(output: Output, port: int) -> None:
    """Say what to check when the page does not open: the port published as is.

    Under the launcher, which publishes the port and opens the browser itself (0178),
    say that instead.

    Args:
        output: Where to tell it.
        port: The port listened on, inside the container.
    """
    if os.environ.get(LAUNCHER_VARIABLE):
        output.info(
            _("Your browser opens on {url}; if not, open that address.").format(
                url=page_url(port)
            )
        )
        return
    output.tip(
        _(
            "The page does not open? docker run must publish the same port on both "
            "sides: -p 127.0.0.1:{port}:{port}."
        ).format(port=port)
    )
