"""`media-hygiene status`: where am I? Read-only, no scan, about a second."""

from __future__ import annotations

import typer

from media_hygiene.cli.context import runtime_of
from media_hygiene.cli.status_next import advise_status
from media_hygiene.cli.status_view import status_lines
from media_hygiene.i18n import _
from media_hygiene.services.status import read_status


def status_command(ctx: typer.Context) -> None:
    """Show the last audit, the quarantine, the reviews left, then the next step.

    Nothing is scanned: only the tool folders are read (reports, journal,
    quarantine, cache). A folder not mounted is said, never an error.

    Args:
        ctx: Typer context holding the runtime.
    """
    runtime = runtime_of(ctx)
    status = read_status(runtime)
    runtime.output.title(_("Where you are"))
    for line in status_lines(status):
        runtime.output.info(line)
    advise_status(runtime, status)
