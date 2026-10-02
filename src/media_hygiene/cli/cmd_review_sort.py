"""`media-hygiene review-sort`: walk through a classify proposal in the browser."""

from __future__ import annotations

from typing import Annotated, Final

import typer

from media_hygiene.cli import review_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _
from media_hygiene.services.sort_reviewing import open_sort_review, serve_sort_review

SORT_REVIEW_PORT: Final = 8080


def review_sort_command(
    ctx: typer.Context,
    workbook: Annotated[
        str | None,
        typer.Argument(
            help=_("The classify workbook; the latest classify run's by default.")
        ),
    ] = None,
    *,
    port: Annotated[int, review_options.port()] = SORT_REVIEW_PORT,
) -> None:
    """Serve the events of a classify proposal in the browser until Ctrl+C.

    Args:
        ctx: Typer context holding the runtime.
        workbook: The workbook (host or container path), or None for the latest.
        port: `--port`, inside the container.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        session = open_sort_review(runtime, workbook)
        if not session.event_count:
            output.success(_("No event in this proposal: nothing to review."))
            return
        serve_sort_review(runtime, session, port)
        events, files = session.progress
        output.blank()
        output.success(
            _(
                "Review stopped — events chosen: {events}, photos chosen one by one: "
                "{files}."
            ).format(events=human_number(events), files=human_number(files))
        )
        output.info(_("Your choices are in {place}.").format(place=session.hosts[1]))
        output.tip(
            _(
                "Next: 'sort' applies them on top of the workbook, which you may "
                "still edit; it refuses an event or a file edited otherwise in both."
            )
        )
