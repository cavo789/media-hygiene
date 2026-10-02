"""`media-hygiene history`: list the runs recorded in the journal."""

from __future__ import annotations

import typer
from rich.table import Table

from media_hygiene.actions.runs import RunSummary, list_run_ids, summarize
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind


def history_command(ctx: typer.Context) -> None:
    """Show every run: its command, files deleted, space freed, moves, restores.

    Args:
        ctx: Typer context holding the runtime.

    Raises:
        MountError: The journal is not mounted.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        if not runtime.persistent(MountKind.JOURNAL):
            raise MountError(
                _("No journal mount: no history to show."),
                _('Mount the journal folder used by clean: -v "<folder>:/journal".'),
            )
        runs = list_run_ids(runtime.locations.journal_dir)
        summaries = [summarize(runtime.locations.journal_dir, run) for run in runs]
    if not summaries:
        output.info(_("No run yet."))
        return
    output.show(_runs_table(summaries))
    output.tip(_("'media-hygiene undo <run>' restores the files of a run."))


def _runs_table(summaries: list[RunSummary]) -> Table:
    """One line per run; the run names stay whole, `undo` needs them.

    Args:
        summaries: The runs, newest first.

    Returns:
        The table; the *Moved* and *Linked* columns only when a run moved files or
        made an album.
    """
    moved = any(run.moved for run in summaries)
    linked = any(run.linked for run in summaries)
    table = Table(title=_("Runs (newest first)"), title_justify="left")
    table.add_column(_("Run"), no_wrap=True)
    table.add_column(_("Command"))
    headers = [_("Deleted"), _("Freed"), _("Quarantined")]
    headers += [_("Moved")] if moved else []
    headers += [_("Linked")] if linked else []
    for header in [*headers, _("Restored")]:
        table.add_column(header, justify="right")
    for run in summaries:
        counts = [human_number(run.deleted), human_size(run.freed)]
        counts += [human_number(run.quarantined)]
        counts += [human_number(run.moved)] if moved else []
        counts += [human_number(run.linked)] if linked else []
        table.add_row(run.run_id, run.kind.value, *counts, human_number(run.restored))
    return table
