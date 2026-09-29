"""`media-hygiene undo`: restore the files of a run (`clean`, later `sort`)."""

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.console.progress import RichProgress
from media_hygiene.console.tables import outcome_table
from media_hygiene.i18n import _
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.clean import CleanService
from media_hygiene.services.undo import resolve_run_id, run_kind, undo_run


def undo_command(
    ctx: typer.Context,
    run_id: Annotated[
        str | None,
        typer.Argument(
            help=_("Run to undo (see 'history'); the latest one by default.")
        ),
    ] = None,
) -> None:
    """Restore every file a run deleted, quarantined or moved.

    Args:
        ctx: Typer context holding the runtime.
        run_id: Run identifier, or None for the latest run.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        run = resolve_run_id(runtime, run_id)
        CleanService(runtime, NullProgress()).ensure_ready()
        title = _("Undo the {command} run {run_id}").format(
            command=run_kind(runtime, run).value, run_id=run
        )
        output.title(title)
        with RichProgress(output.console) as progress:
            outcome = undo_run(runtime, run, progress)
    output.show(outcome_table(outcome, title))
    for incident in outcome.skipped:
        output.warning(f"{runtime.mapper.to_host(incident.path)}: {incident.reason}")
    for incident in outcome.failed:
        output.error(f"{runtime.mapper.to_host(incident.path)}: {incident.reason}")
