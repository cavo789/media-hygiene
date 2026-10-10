"""`review --near` in the terminal: what is to decide, then what comes next."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.next_steps import carried, suggest
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.place import decisions_flag
from media_hygiene.services.next_command import CHANGING, NextVerb

if TYPE_CHECKING:
    import typer

    from media_hygiene.review.near_session import NearSession
    from media_hygiene.services.runtime import Runtime


def tell_near_opened(runtime: Runtime, session: NearSession) -> None:
    """Say how many groups are sure and how many are to check, and what changed.

    Args:
        runtime: Settings, mount points and output.
        session: The review, opened.
    """
    output = runtime.output
    groups = session.state().groups
    sure = sum(group.sure for group in groups)
    message = ngettext(
        "{count} group of near duplicates: {sure} sure, {look} to check (shown first).",
        "{count} groups of near duplicates: {sure} sure, {look} to check (shown "
        "first).",
        len(groups),
    )
    output.info(
        message.format(
            count=human_number(len(groups)),
            sure=human_number(sure),
            look=human_number(len(groups) - sure),
        )
    )
    if session.dropped:
        dropped = ngettext(
            "{count} group decided earlier changed since: to decide again.",
            "{count} groups decided earlier changed since: to decide again.",
            session.dropped,
        )
        output.warning(dropped.format(count=human_number(session.dropped)))


def tell_near_stopped(
    ctx: typer.Context, runtime: Runtime, session: NearSession
) -> None:
    """Sum the review up once stopped, and say what comes next.

    Args:
        ctx: Typer context of the review, whose options `clean` keeps.
        runtime: Settings, mount points and output.
        session: The review, stopped.
    """
    output = runtime.output
    decided, total = session.decided
    output.blank()
    output.success(
        _("Review stopped — groups decided: {decided} of {total}.").format(
            decided=human_number(decided), total=human_number(total)
        )
    )
    place = session.place
    output.info(_("Your choices are in {place}.").format(place=place.host))
    flag = decisions_flag(place.argument)
    suggest(
        runtime,
        _(
            "the same 'clean' command with --tier near {option}; the sure groups "
            "and those you decided go to the quarantine, 'undo' brings them back."
        ).format(option=flag),
        NextVerb(carried(runtime, f"clean --tier near {flag}", ctx), CHANGING),
    )
