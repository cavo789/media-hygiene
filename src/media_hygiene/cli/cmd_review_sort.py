"""`media-hygiene review-sort`: walk through a classify proposal in the browser."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from media_hygiene.cli import review_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.review.sort_batch import SortBatchSession


def review_sort_command(
    ctx: typer.Context,
    workbook: Annotated[
        str | None,
        typer.Argument(
            help=_("The classify workbook; the latest classify run's by default.")
        ),
    ] = None,
    *,
    port: Annotated[int | None, review_options.port()] = None,
) -> None:
    """Serve the events of a classify proposal in the browser until Ctrl+C.

    Args:
        ctx: Typer context holding the runtime.
        workbook: The workbook (host or container path), or None for the latest.
        port: `--port`, inside the container.
    """
    from media_hygiene.cli.next_steps import carried, suggest
    from media_hygiene.console.formatting import human_number
    from media_hygiene.services.next_command import CHANGING, NextVerb
    from media_hygiene.services.sort_reviewing import (
        open_sort_review,
        serve_sort_review,
    )

    runtime = runtime_of(ctx)
    port = review_options.page_port(runtime, port)
    output = runtime.output
    with user_errors(output):
        session = open_sort_review(runtime, workbook)
        if not session.event_count:
            output.success(_("No event in this proposal: nothing to review."))
            return
        _tell_sure(output, session)
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
        verb = "sort" if workbook is None else f'sort "{workbook}"'
        suggest(
            runtime,
            _(
                "'sort' applies them on top of the workbook, which you may still "
                "edit; it refuses an event or a file edited otherwise in both."
            ),
            NextVerb(carried(runtime, verb), CHANGING),
        )


def _tell_sure(output: Output, session: SortBatchSession) -> None:
    """Say how many events still to decide have a sure proposal, accepted by one click.

    Args:
        output: Where to tell it.
        session: The review, opened.
    """
    from media_hygiene.console.formatting import human_number

    open_events, sure = session.open_and_sure()
    if not open_events:
        return
    message = ngettext(
        "{count} event to decide: {sure} with a sure proposal (one click), {look} to "
        "look at.",
        "{count} events to decide: {sure} with a sure proposal (one click), {look} to "
        "look at.",
        open_events,
    )
    output.info(
        message.format(
            count=human_number(open_events),
            sure=human_number(sure),
            look=human_number(open_events - sure),
        )
    )
