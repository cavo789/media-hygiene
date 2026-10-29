"""What `review` says of its burst series: before serving it, once stopped."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.next_steps import carried, suggest
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.place import decisions_flag
from media_hygiene.services.next_command import CHANGING, NextVerb

if TYPE_CHECKING:
    import typer

    from media_hygiene.console.output import Output
    from media_hygiene.review.session import ReviewSession
    from media_hygiene.services.runtime import Runtime


def tell_obvious(output: Output, session: ReviewSession) -> None:
    """Say how many series still to see are obvious, validated by one click.

    Args:
        output: Where to tell it.
        session: The review, opened.
    """
    todo = [item for item in session.state().series if not item.reviewed]
    if not todo:
        return
    obvious = sum(1 for item in todo if item.obvious)
    message = ngettext(
        "{count} series to see: {obvious} (one click), {look} to look at.",
        "{count} series to see: {obvious} (one click), {look} to look at.",
        len(todo),
    )
    output.info(
        message.format(
            count=human_number(len(todo)),
            obvious=ngettext("{count} obvious", "{count} obvious", obvious).format(
                count=human_number(obvious)
            ),
            look=human_number(len(todo) - obvious),
        )
    )


def tell_stopped(ctx: typer.Context, runtime: Runtime, session: ReviewSession) -> None:
    """Sum the review up once stopped, and say what comes next.

    Args:
        ctx: Typer context of the review, whose options `clean` keeps.
        runtime: Settings, mount points and output.
        session: The review, stopped.
    """
    output = runtime.output
    series, shots = session.progress
    output.blank()
    output.success(
        _(
            "Review stopped — series with shots set aside: {series}, shots set "
            "aside: {shots}."
        ).format(series=human_number(series), shots=human_number(shots))
    )
    seen, total = session.seen
    output.info(
        _("Series seen: {seen} of {total}.").format(
            seen=human_number(seen), total=human_number(total)
        )
    )
    place = session.place
    output.info(_("Your choices are in {place}.").format(place=place.host))
    if shots:
        flag = decisions_flag(place.argument)
        suggest(
            runtime,
            _(
                "the same 'clean' command with {option}; the shots set aside go "
                "to the quarantine, 'undo' brings them back."
            ).format(option=flag),
            NextVerb(carried(runtime, f"clean {flag}", ctx), CHANGING),
        )
