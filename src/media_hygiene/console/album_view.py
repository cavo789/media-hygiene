"""The console side of `album`: what it gathers, what it links, how to undo it."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.markup import escape
from rich.table import Table

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.services.album import AlbumPrepared, AlbumResult
    from media_hygiene.services.runtime import Runtime

_SHOWN: Final = 10


def show_album(runtime: Runtime, prepared: AlbumPrepared) -> None:
    """Say what the album gathers, before any link is made.

    Args:
        runtime: Settings, mount points and output.
        prepared: The album.
    """
    output, host = runtime.output, runtime.mapper.to_host
    plan = prepared.plan
    output.info(_("Workbook: {path}").format(path=host(prepared.workbook)))
    table = Table(show_header=False, title_justify="left")
    table.add_column(style="bold")
    table.add_column(justify="right")
    table.add_row(_("Album folder"), escape(host(plan.folder)))
    table.add_row(_("Files selected"), human_number(prepared.selected))
    table.add_row(_("Links to make"), human_number(len(plan.links)))
    table.add_row(_("In the album already"), human_number(len(plan.present)))
    table.add_row(_("Not found"), human_number(len(plan.missing)))
    table.add_row(_("On another disk or mount"), human_number(len(plan.elsewhere)))
    output.show(table)
    _list(runtime, plan.missing, _("not found where the plan or a sort put it"))
    _list(runtime, plan.elsewhere, _("on another disk or mount: no link possible"))
    if plan.missing:
        output.tip(_("Run 'classify' again: its plan sees the files where they are."))
    if plan.elsewhere:
        output.tip(
            _(
                "A hard link stays on the disk and in the mounted folder of its file: "
                "set album.root to a folder inside the one mounted for these photos."
            )
        )


def _list(runtime: Runtime, paths: Sequence[Path], reason: str) -> None:
    """Warn about the first files set aside, and say how many more.

    Args:
        runtime: Settings, mount points and output.
        paths: The files (container paths).
        reason: Why they are set aside, translated.
    """
    output, host = runtime.output, runtime.mapper.to_host
    for path in paths[:_SHOWN]:
        output.warning(escape(f"{host(path)}: {reason}"))
    if len(paths) > _SHOWN:
        output.info(
            _("... and {count} more.").format(count=human_number(len(paths) - _SHOWN))
        )


def show_album_result(runtime: Runtime, result: AlbumResult) -> None:
    """Say what the run made, what failed, and how to undo it.

    Args:
        runtime: Settings, mount points and output.
        result: The run.
    """
    output, host = runtime.output, runtime.mapper.to_host
    outcome = result.outcome
    output.success(
        ngettext(
            "{count} link made: no photo was copied nor moved, no space is used.",
            "{count} links made: no photo was copied nor moved, no space is used.",
            outcome.done,
        ).format(count=human_number(outcome.done))
    )
    for incident in outcome.failed[:_SHOWN]:
        output.error(escape(f"{host(incident.path)}: {incident.reason}"))
    if result.ended.unsupported:
        output.error(_("The album stopped at the first link refused by the disk."))
    if result.ended.interrupted:
        output.warning(_("Stopped before the end, as asked."))
        output.tip(_("Run the same command again: the files linked are skipped."))
    output.tip(
        _(
            "'media-hygiene undo {run_id}' removes the album; the photos stay "
            "where they are."
        ).format(run_id=result.run_id)
    )
