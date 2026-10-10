"""`media-hygiene review`: set burst shots aside, series by series, in the browser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Final

import typer

from media_hygiene.cli import options, review_options
from media_hygiene.cli.context import folder_layer, runtime_of, user_errors
from media_hygiene.cli.flows import audit_and_show
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.place import DEFAULT_DECISIONS, decisions_flag
from media_hygiene.services.reviewing import open_review, review_target, serve_review

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.review.session import ReviewSession

_DECISIONS_FILE: Final = Path(DEFAULT_DECISIONS)


# The options are parameters: the documented exception for Typer commands.
def review_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    prefer: Annotated[list[str] | None, options.prefer()] = None,
    protect: Annotated[list[str] | None, options.protect()] = None,
    exclude: Annotated[list[str] | None, options.exclude()] = None,
    decisions: Annotated[Path, review_options.decisions_file()] = _DECISIONS_FILE,
    port: Annotated[int, review_options.port()] = review_options.PAGE_PORT,
) -> None:
    """Audit, then serve the burst series in the browser until Ctrl+C.

    Args:
        ctx: Typer context holding the runtime.
        prefer: `--prefer` folders.
        protect: `--protect` folders.
        exclude: `--exclude` folders.
        decisions: `--decisions`, the file to save the decisions in.
        port: `--port`, inside the container.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        runtime = runtime.with_overrides(folder_layer(prefer, protect, exclude))
        target = review_target(runtime, decisions)
        findings = audit_and_show(runtime)
        if not findings.similar.bursts:
            output.success(_("No burst series: nothing to review."))
            return
        session = open_review(runtime, findings, target)
        _tell_obvious(output, session)
        if session.dropped:
            dropped = ngettext(
                "{count} series reviewed earlier changed since: reviewed again.",
                "{count} series reviewed earlier changed since: reviewed again.",
                session.dropped,
            )
            output.warning(dropped.format(count=human_number(session.dropped)))
        serve_review(runtime, session, port)
        _tell_stopped(output, session)


def _tell_obvious(output: Output, session: ReviewSession) -> None:
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
        "{count} series to see: {obvious} obvious (one click), {look} to look at.",
        "{count} series to see: {obvious} obvious (one click), {look} to look at.",
        len(todo),
    )
    output.info(
        message.format(
            count=human_number(len(todo)),
            obvious=human_number(obvious),
            look=human_number(len(todo) - obvious),
        )
    )


def _tell_stopped(output: Output, session: ReviewSession) -> None:
    """Sum the review up once stopped, and say what comes next.

    Args:
        output: Where to tell it.
        session: The review, stopped.
    """
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
        output.next_step(
            _(
                "the same 'clean' command with {option}; the shots set aside go "
                "to the quarantine, 'undo' brings them back."
            ).format(option=decisions_flag(place.argument))
        )
