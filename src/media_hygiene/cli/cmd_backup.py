r"""`media-hygiene backup`: what `mh backup` would copy into its NAS folder (0264).

The copy itself is made by Windows (`mh backup`, `mh_backup.ps1.j2`), which writes to
the NAS about 7 times faster than a copy through Docker (measured, step 21 of
`mh-measure.ps1`). Run by hand, this command only shows the plan: it reads the photo
folders and the target, mounted read-only, and changes nothing.
"""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import folder_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _

_TO_HELP = _(
    "The backup folder, as Windows writes it (\\\\NAS\\backup_photos): a folder "
    "of its own, never a photo folder nor a backup compared."
)
_ANYWAY_HELP = _(
    "Go on even when more than stop_above_percent (config.toml) of the backup "
    "would be set aside or replaced."
)


def backup_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    to: Annotated[str, typer.Option("--to", help=_TO_HELP, show_default=False)],
    anyway: Annotated[bool, typer.Option("--anyway", help=_ANYWAY_HELP)] = False,
    backup: Annotated[list[str] | None, folder_options.kept_backup()] = None,
) -> None:
    """Show what mh backup copies into its folder on the NAS; Windows copies it.

    Args:
        ctx: Typer context holding the runtime.
        to: `--to`, the target.
        anyway: `--anyway`, past the safety stop.
        backup: `--backup` folders, which the target must not overlap.
    """
    from media_hygiene.console.backup_target_view import show_plan
    from media_hygiene.services.backup_run import prepare_backup

    runtime = runtime_of(ctx).with_overrides(folder_options.backup_layer(backup))
    output = runtime.output
    output.info(_("🔒 Only read: your photos and the backup folder are not changed."))
    with user_errors(output):
        prepared = prepare_backup(runtime, to, anyway=anyway)
    show_plan(output, prepared)
    output.next_step(
        _(
            "in Windows PowerShell, type mh backup --to {target}: Windows copies, "
            "about 7 times faster than Docker."
        ).format(target=prepared.target.host)
    )
