"""`media-hygiene review`: set burst shots aside, series by series, in the browser.

The other pages (`--near`, `--pairs`, `--junk`, `--gone`, `--intruders`) are
dispatched by `review_modes`.
"""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Final

import typer

from media_hygiene.cli import (
    folder_options,
    import_options,
    options,
    review_options,
    scan_options,
)
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.folder_options import FolderOptions
from media_hygiene.cli.scan_options import scan_layer
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.place import DEFAULT_DECISIONS

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
    imported: Annotated[
        str | None, import_options.imported(options.panel_advanced())
    ] = None,
    since: Annotated[str | None, import_options.since(options.panel_advanced())] = None,
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
        imported: `--imported`, an import's folder: its burst series only (0480).
        since: `--since`, the import's period.
    """
    from media_hygiene.cli.apply_step import end_on_applied, page_apply
    from media_hygiene.cli.flows import audit_and_show
    from media_hygiene.cli.review_modes import (
        ReviewMode,
        ReviewRun,
        review_mode,
        run_mode,
    )
    from media_hygiene.cli.review_tells import tell_obvious, tell_stopped
    from media_hygiene.console.formatting import human_number
    from media_hygiene.review.apply_api import ReviewStart
    from media_hygiene.services.import_bursts import IMPORT_DECISIONS, import_bursts
    from media_hygiene.services.import_end import imported as imported_files
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
        if imported is not None and decisions == _DECISIONS_FILE:
            decisions = Path(IMPORT_DECISIONS)
        target = review_target(runtime, decisions, port)
        findings = audit_and_show(runtime)
        if imported is not None:
            findings = import_bursts(findings, imported_files(runtime, imported, since))
        if mode is not ReviewMode.BURSTS:
            run_mode(ReviewRun(ctx, runtime, target, port), mode, findings)
            return
        if not findings.similar.bursts:
            output.success(_("No burst series: nothing to review."))
            return
        session = open_review(runtime, findings, target)
        tell_obvious(output, session)
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
        tell_stopped(ctx, runtime, session)
