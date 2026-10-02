"""`media-hygiene inventory`: every photo and video with what the audits learnt."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Final

import typer
from rich.table import Table

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.console.formatting import human_number
from media_hygiene.constants import InventoryFormat
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.inventory import export_inventory
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.services.inventory import InventoryResult

_DATE: Final = "%Y-%m-%d %H:%M"


def inventory_command(
    ctx: typer.Context,
    file_format: Annotated[
        InventoryFormat,
        typer.Option(
            "--format",
            help=_(
                "xlsx: an Excel workbook (Files and Summary sheets). csv: the Files"
                " sheet only, like plan.csv. Default: xlsx."
            ),
            show_default=False,
            case_sensitive=False,
        ),
    ] = InventoryFormat.XLSX,
) -> None:
    """Export the index to a workbook: one row per file, without reading any file.

    Args:
        ctx: Typer context holding the runtime.
        file_format: `--format`, the workbook or a CSV file.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        # The index is upgraded in place when an older version wrote it.
        ensure_writable(runtime, MountKind.CACHE, MountKind.REPORTS)
        result = export_inventory(runtime, file_format)
    files = result.summary.files
    output.success(
        ngettext(
            "Inventory of {count} file written: {path}",
            "Inventory of {count} files written: {path}",
            files,
        ).format(count=human_number(files), path=runtime.mapper.to_host(result.target))
    )
    output.show(_roots_table(result, runtime.mapper))
    if not result.roots:
        output.tip(
            _("Run 'audit' on your folders: the inventory then says how fresh it is.")
        )


def _roots_table(result: InventoryResult, mapper: HostPathMapper) -> Table:
    """How fresh the inventory is: when each folder was last audited completely.

    Args:
        result: What was exported.
        mapper: Host/container path translator.

    Returns:
        The table.
    """
    table = Table(title=_("Last complete audit (UTC)"), title_justify="left")
    table.add_column(_("Folder"))
    table.add_column(_("Date"), no_wrap=True)
    for root in result.roots:
        table.add_row(mapper.to_host(root.path), root.walked_at.strftime(_DATE))
    return table
