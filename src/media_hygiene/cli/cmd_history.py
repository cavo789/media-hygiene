"""`media-hygiene history`: list the runs recorded in the journal."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import TYPE_CHECKING

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from rich.table import Table

    from media_hygiene.services.history_rows import HistoryTable


def history_command(ctx: typer.Context) -> None:
    """Show every run: its command, files deleted, space freed, moves, restores.

    Args:
        ctx: Typer context holding the runtime.
    """
    from media_hygiene.services.history_rows import history_table, load_runs

    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        summaries = load_runs(runtime)
    if not summaries:
        output.info(_("No run yet."))
        return
    table = history_table(summaries)
    output.show(_runs_table(table))
    for note in table.notes:
        output.info(note)
    output.tip(_("'media-hygiene undo <run>' restores the files of a run."))


def _runs_table(history: HistoryTable) -> Table:
    """One line per run; the run names stay whole, `undo` needs them.

    Args:
        history: The rows (`history_rows`), shared with the home page.

    Returns:
        The table; the optional columns (unwanted, back again, Explorer, moved,
        linked, sidecars, folders removed, copied) only when a run has something
        in them.
    """
    from rich.table import Table

    table = Table(title=_("Runs (newest first)"), title_justify="left")
    table.add_column(_("Run"), no_wrap=True)
    table.add_column(_("Command"))
    for header in history.figures:
        table.add_column(header, justify="right")
    for row in history.rows:
        table.add_row(row.run_id, row.command, *row.cells)
    return table
