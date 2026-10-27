"""`media-hygiene history`: list the runs recorded in the journal."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import TYPE_CHECKING

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable

    from rich.table import Table

    from media_hygiene.actions.runs import RunSummary


def history_command(ctx: typer.Context) -> None:
    """Show every run: its command, files deleted, space freed, moves, restores.

    Args:
        ctx: Typer context holding the runtime.

    Raises:
        MountError: The journal is not mounted.
    """
    from media_hygiene.actions.kinds import Phase
    from media_hygiene.actions.runs import list_run_ids, summarize
    from media_hygiene.errors import MountError
    from media_hygiene.paths.mount_kind import MountKind

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
    if any(run.kind is Phase.PUSH for run in summaries):
        output.info(
            _(
                "🛟 A backup run changed its backup folder only, never your photos: "
                "mh push --undo <run> puts back what it renamed or set aside there."
            )
        )
    if any(run.kind is Phase.PHONE for run in summaries):
        output.info(
            _(
                "📱 A phone run deleted files from a phone: undo cannot put them "
                "back on it. Each one was first proven on the PC by its content."
            )
        )
    output.tip(_("'media-hygiene undo <run>' restores the files of a run."))


def _runs_table(summaries: list[RunSummary]) -> Table:
    """One line per run; the run names stay whole, `undo` needs them.

    Args:
        summaries: The runs, newest first.

    Returns:
        The table; the *Unwanted*, *Back*, *Explorer*, *Moved*, *Linked*,
        *Sidecars* and *Folders removed* columns only when a run set unwanted
        photos aside, set aside again files that came back, marked files deleted
        in the Explorer, moved files, made an album, wrote sidecars or removed the
        folders it left empty; *Copied* (bytes) when `import` or `mh push` ran.
    """
    from rich.table import Table

    from media_hygiene.console.formatting import human_number, human_size

    optional: list[tuple[str, Callable[[RunSummary], int]]] = [
        (_("Of which unwanted"), lambda run: run.unwanted),
        (_("Of which back again"), lambda run: run.returned),
        (_("Deleted in the Explorer"), lambda run: run.marked),
        (_("Moved"), lambda run: run.moved),
        (_("Linked"), lambda run: run.linked),
        (_("Sidecars"), lambda run: run.kept.written),
        (_("Folders removed"), lambda run: run.folders_removed),
        (_("Copied"), lambda run: run.kept.copied),  # bytes: import, mh push
    ]
    shown = [(h, count) for h, count in optional if any(map(count, summaries))]
    sizes = {_("Copied")}
    table = Table(title=_("Runs (newest first)"), title_justify="left")
    table.add_column(_("Run"), no_wrap=True)
    table.add_column(_("Command"))
    headers = [_("Deleted"), _("Freed"), _("Quarantined")]
    for header in [*headers, *(header for header, _count in shown), _("Restored")]:
        table.add_column(header, justify="right")
    for run in summaries:
        counts = [human_number(run.deleted), human_size(run.freed)]
        counts += [human_number(run.quarantined)]
        counts += [
            (human_size if header in sizes else human_number)(count(run))
            for header, count in shown
        ]
        table.add_row(run.run_id, run.kind.value, *counts, human_number(run.restored))
    return table
