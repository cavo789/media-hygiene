"""`review --junk` in the terminal: what is to decide, then what comes next."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from media_hygiene.cli.review_next import CleanNext, tell_choices_and_clean
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    import typer

    from media_hygiene.review.unwanted_session import UnwantedSession
    from media_hygiene.services.runtime import Runtime


def tell_unwanted_opened(runtime: Runtime, session: UnwantedSession) -> None:
    """Say how many photos look unwanted, by reason, and what changed.

    Args:
        runtime: Settings, mount points and output.
        session: The review, opened.
    """
    output = runtime.output
    state = session.state()
    counts = Counter(photo.reason for photo in state.photos)
    reasons = ", ".join(
        f"{state.reasons[reason]}: {human_number(count)}"
        for reason, count in counts.most_common()
    )
    message = ngettext(
        "{count} photo looks unwanted ({reasons}); nothing is set aside without you.",
        "{count} photos look unwanted ({reasons}); nothing is set aside without you.",
        len(state.photos),
    )
    output.info(message.format(count=human_number(len(state.photos)), reasons=reasons))
    if session.dropped:
        dropped = ngettext(
            "{count} photo decided earlier is no longer listed or changed since: "
            "its decision is dropped.",
            "{count} photos decided earlier are no longer listed or changed since: "
            "their decisions are dropped.",
            session.dropped,
        )
        output.warning(dropped.format(count=human_number(session.dropped)))


def tell_unwanted_stopped(
    ctx: typer.Context, runtime: Runtime, session: UnwantedSession
) -> None:
    """Sum the review up once stopped, and say what comes next.

    Args:
        ctx: Typer context of the review, whose options `clean` keeps.
        runtime: Settings, mount points and output.
        session: The review, stopped.
    """
    output = runtime.output
    decided, aside, total = session.decided
    output.blank()
    output.success(
        _(
            "Review stopped — photos decided: {decided} of {total}, set aside: {aside}."
        ).format(
            decided=human_number(decided),
            total=human_number(total),
            aside=human_number(aside),
        )
    )
    if not aside:
        output.info(_("Your choices are in {place}.").format(place=session.place.host))
        return
    text = _(
        "the same 'clean' command with {option}; the photos set aside go to "
        "the quarantine, 'undo' brings them back."
    )
    tell_choices_and_clean(ctx, runtime, CleanNext(session.place, text))
