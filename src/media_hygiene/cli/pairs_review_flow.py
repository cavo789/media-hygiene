"""`review --pairs` in the terminal: what is to decide, then what comes next."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.review_next import CleanNext, tell_choices_and_clean
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.plan.review import PairAction

if TYPE_CHECKING:
    import typer

    from media_hygiene.review.pairs_session import PairsSession
    from media_hygiene.services.runtime import Runtime


def tell_pairs_opened(runtime: Runtime, session: PairsSession) -> None:
    """Say how many pairs there are and how many are decided, and what changed.

    Args:
        runtime: Settings, mount points and output.
        session: The review, opened.
    """
    output = runtime.output
    decided, total = session.decided
    message = ngettext(
        "{count} folder pair, the most space freed first: {decided} decided already.",
        "{count} folder pairs, the most space freed first: {decided} decided already.",
        total,
    )
    output.info(
        message.format(count=human_number(total), decided=human_number(decided))
    )
    if session.dropped:
        dropped = ngettext(
            "{count} pair decided earlier no longer exists: its decision is dropped.",
            "{count} pairs decided earlier no longer exist: their decisions are "
            "dropped.",
            session.dropped,
        )
        output.warning(dropped.format(count=human_number(session.dropped)))


def tell_pairs_stopped(
    ctx: typer.Context, runtime: Runtime, session: PairsSession
) -> None:
    """Sum the review up once stopped, and say what comes next.

    Args:
        ctx: Typer context of the review, whose options `clean` keeps.
        runtime: Settings, mount points and output.
        session: The review, stopped.
    """
    output = runtime.output
    decided, total = session.decided
    changing = sum(
        pair.action not in {"", PairAction.PLANNED} for pair in session.state().pairs
    )
    output.blank()
    output.success(
        _(
            "Review stopped — pairs decided: {decided} of {total}, swapped or left "
            "alone: {changing}."
        ).format(
            decided=human_number(decided),
            total=human_number(total),
            changing=human_number(changing),
        )
    )
    text = _(
        "the same 'clean' command with {option}; it applies your pairs, and "
        "'undo' brings back what it removed."
    )
    tell_choices_and_clean(ctx, runtime, CleanNext(session.place, text))
