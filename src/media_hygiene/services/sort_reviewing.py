"""`media-hygiene review-sort`: walk through a classify proposal, event by event.

The page reads the same workbook `sort` would apply (the latest classify run's by
default) and its plan; its choices go to `sort-decisions.json` next to `plan.json`,
never into the workbook: Excel may have it open. `sort` lays them over the workbook's
edits (`classify/page_overlay`).
"""

from __future__ import annotations

import asyncio
import contextlib
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.page_overlay import overlay
from media_hygiene.classify.workbook.reader import read_edits
from media_hygiene.console.formatting import human_number
from media_hygiene.errors import MountError
from media_hygiene.i18n import _, ngettext
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.paths.mounts import is_writable
from media_hygiene.review.sort_app import PAGE_PATH, STATE_PATH, SortReviewApp
from media_hygiene.review.sort_choices import EVENT_PATH, FILES_PATH, FORGET_PATH
from media_hygiene.review.sort_files import SortSource
from media_hygiene.review.sort_session import SortSession
from media_hygiene.services.page_choices import page_decisions, page_file
from media_hygiene.services.reviewing import address_tip, run_server
from media_hygiene.services.sort_inputs import find_workbook, open_elsewhere, plan_of
from media_hygiene.services.writable import writable_tip

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

_TEMPLATES_PACKAGE: Final = "media_hygiene.review"
_PAGE_TEMPLATE: Final = "sort_review.html.j2"


def open_sort_review(runtime: Runtime, given: str | None) -> SortSession:
    """Read the workbook, its plan and the page's earlier choices.

    Args:
        runtime: Settings, mount points and output.
        given: The workbook named (host or container path), or None for the latest.

    Returns:
        The session.

    Raises:
        MountError: The choices could not be saved next to `plan.json`.
    """
    workbook = find_workbook(runtime, given)
    plan_file, plan = plan_of(runtime, workbook)
    if not is_writable(plan_file.parent):
        folder = runtime.mapper.to_host(plan_file.parent)
        raise MountError(
            _("The container cannot write to {folders}.").format(folders=folder),
            writable_tip([plan_file.parent]),
        )
    edits = read_edits(workbook, plan)
    base = page_decisions(plan_file, plan)
    target = page_file(plan_file)
    output, host = runtime.output, runtime.mapper.to_host
    if open_elsewhere(workbook):
        output.warning(
            _(
                "The workbook is open in Excel or LibreOffice: what is not saved is "
                "not shown."
            )
        )
    conflicts = overlay(edits, base).conflicts
    if conflicts:
        message = ngettext(
            "{count} earlier choice of the page was edited otherwise in the workbook "
            "since: shown in red, choose again.",
            "{count} earlier choices of the page were edited otherwise in the "
            "workbook since: shown in red, choose again.",
            len(conflicts),
        )
        output.warning(message.format(count=human_number(len(conflicts))))
    source = SortSource(
        plan, edits, target, (host(workbook), host(target)), runtime.mapper
    )
    return SortSession(source, base)


def serve_sort_review(runtime: Runtime, session: SortSession, port: int) -> None:
    """Serve the page until Ctrl+C; every choice is saved as it is made.

    Args:
        runtime: Settings, mount points and output.
        session: The review.
        port: The port to listen on, inside the container (0: any free one).
    """
    environment = translated_environment(_TEMPLATES_PACKAGE, escaped=("html", "j2"))
    workbook, decisions = session.hosts
    page = environment.get_template(_PAGE_TEMPLATE).render(
        paths={
            "page": PAGE_PATH,
            "state": STATE_PATH,
            "event": EVENT_PATH,
            "files": FILES_PATH,
            "forget": FORGET_PATH,
        },
        workbook=workbook,
        decisions=decisions,
    )
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = SortReviewApp(session, page.encode(), executor)
        asyncio.run(run_server(app, port, partial(_announce, runtime, session)))


def _announce(runtime: Runtime, session: SortSession, port: int) -> None:
    """Tell where the page is and how to open it from the host.

    Args:
        runtime: Settings, mount points and output.
        session: The review.
        port: The port listened on, inside the container.
    """
    output = runtime.output
    output.success(
        _(
            "Review ready on port {port}: each choice is saved at once in {place}. "
            "Ctrl+C stops the review."
        ).format(port=port, place=session.hosts[1])
    )
    address_tip(output, port)
