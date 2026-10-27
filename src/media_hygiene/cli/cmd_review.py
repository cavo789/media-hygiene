"""`media-hygiene review`: set burst shots aside, series by series, in the browser.

The other pages (`--near`, `--pairs`, `--junk`, `--gone`, `--intruders`) are
dispatched by `review_modes`.
"""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Final

import typer

from media_hygiene.cli import folder_options, options, review_options, scan_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.folder_options import FolderOptions
from media_hygiene.cli.scan_options import scan_layer
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.place import DEFAULT_DECISIONS

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.review.session import ReviewSession
    from media_hygiene.services.runtime import Runtime

_DECISIONS_FILE: Final = Path(DEFAULT_DECISIONS)


# The options are parameters: the documented exception for Typer commands.
def review_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    near: Annotated[bool, review_options.near()] = False,
    pairs: Annotated[bool, review_options.pairs()] = False,
    junk: Annotated[bool, review_options.junk()] = False,
    gone: Annotated[bool, review_options.gone()] = False,
    intruders: Annotated[bool, review_options.intruders()] = False,
    decisions: Annotated[Path, review_options.decisions_file()] = _DECISIONS_FILE,
    port: Annotated[int | None, review_options.port(options.panel_advanced())] = None,
    prefer: Annotated[list[str] | None, folder_options.prefer()] = None,
    protect: Annotated[list[str] | None, folder_options.protect()] = None,
    exclude: Annotated[list[str] | None, folder_options.exclude()] = None,
    backup: Annotated[list[str] | None, folder_options.backup()] = None,
    ext: Annotated[list[str] | None, scan_options.extensions()] = None,
    exclude_name: Annotated[list[str] | None, scan_options.exclude_name()] = None,
) -> None:
    """Audit, then serve the burst series (near duplicates, pairs) until Ctrl+C.

    Args:
        ctx: Typer context holding the runtime.
        prefer: `--prefer` folders.
        protect: `--protect` folders.
        exclude: `--exclude` folders.
        backup: `--backup` folders, compared and never changed.
        ext: `--ext` categories and extensions, as for `audit`.
        exclude_name: `--exclude-name` folder names, as for `audit`.
        decisions: `--decisions`, the file to save the decisions in.
        port: `--port`, inside the container.
        near: `--near`, the near duplicates instead of the burst series.
        pairs: `--pairs`, the folder pairs instead of the burst series.
        junk: `--junk`, the photos most likely unwanted instead.
        gone: `--gone`, the files gone since the last audit instead.
        intruders: `--intruders`, the files neither photos nor videos instead.
    """
    from media_hygiene.cli.apply_step import end_on_applied, page_apply
    from media_hygiene.cli.flows import audit_and_show
    from media_hygiene.cli.review_modes import (
        ReviewMode,
        ReviewRun,
        review_mode,
        run_mode,
    )
    from media_hygiene.console.formatting import human_number
    from media_hygiene.review.apply_api import ReviewStart
    from media_hygiene.services.reviewing import (
        open_review,
        review_target,
        serve_review,
    )

    runtime = runtime_of(ctx)
    port = review_options.page_port(runtime, port)
    output = runtime.output
    with user_errors(output):
        runtime = runtime.with_overrides(
            FolderOptions(prefer, protect, exclude, backup).layer()
        ).with_overrides(scan_layer(ext, exclude_name))
        mode = review_mode(
            {
                ReviewMode.NEAR: near,
                ReviewMode.PAIRS: pairs,
                ReviewMode.JUNK: junk,
                ReviewMode.GONE: gone,
                ReviewMode.INTRUDERS: intruders,
            }
        )
        target = review_target(runtime, decisions, port)
        findings = audit_and_show(runtime)
        if mode is not ReviewMode.BURSTS:
            run_mode(ReviewRun(ctx, runtime, target, port), mode, findings)
            return
        if not findings.similar.bursts:
            output.success(_("No burst series: nothing to review."))
            return
        session = open_review(runtime, findings, target)
        _tell_obvious(output, session)
        if session.dropped:
            output.warning(
                ngettext(
                    "{count} series reviewed earlier changed since: reviewed again.",
                    "{count} series reviewed earlier changed since: reviewed again.",
                    session.dropped,
                ).format(count=human_number(session.dropped))
            )
        # Opened from the home page: `mh` runs the step *Apply now* ends on (0288).
        code = serve_review(runtime, session, ReviewStart(port, page_apply(runtime)))
        end_on_applied(runtime, code)
        _tell_stopped(ctx, runtime, session)


def _tell_obvious(output: Output, session: ReviewSession) -> None:
    """Say how many series still to see are obvious, validated by one click.

    Args:
        output: Where to tell it.
        session: The review, opened.
    """
    from media_hygiene.console.formatting import human_number

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


def _tell_stopped(ctx: typer.Context, runtime: Runtime, session: ReviewSession) -> None:
    """Sum the review up once stopped, and say what comes next.

    Args:
        ctx: Typer context of the review, whose options `clean` keeps.
        runtime: Settings, mount points and output.
        session: The review, stopped.
    """
    from media_hygiene.cli.next_steps import carried, suggest
    from media_hygiene.console.formatting import human_number
    from media_hygiene.review.place import decisions_flag
    from media_hygiene.services.next_command import CHANGING, NextVerb

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
