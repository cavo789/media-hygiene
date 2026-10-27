"""`media-hygiene import`: copy into the photos what only a folder holds (NAS, disk)."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import folder_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _


def import_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    folder: Annotated[
        str | None,
        typer.Argument(
            help=_(
                "Folder to import from (host path): your NAS, a USB disk, an SD card, "
                "an old disk; only read. Default: your backup folders."
            ),
            show_default=False,
        ),
    ] = None,
    *,
    to: Annotated[
        str | None,
        typer.Option(
            "--to",
            help=_(
                "Folder receiving the copies (host path); default: 'From <source>' in "
                "your first photo folder (From NAS, From E), its folders kept below it."
            ),
            show_default=False,
        ),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help=_("Copy without asking first.")),
    ] = False,
    backup: Annotated[list[str] | None, folder_options.backup()] = None,
) -> None:
    """Copy what only a folder holds, never what you set aside or deleted before.

    Args:
        ctx: Typer context holding the runtime.
        folder: The folder to import from, instead of the backup folders.
        to: `--to`, the folder receiving the copies.
        yes: `--yes`, no question.
        backup: `--backup` folders, compared and never changed.

    Raises:
        typer.Exit: The user declined.
    """
    from media_hygiene.cli.next_steps import carried, safety, suggest
    from media_hygiene.console.import_view import show_plan, show_result
    from media_hygiene.console.progress import RichProgress
    from media_hygiene.scan.progress import NullProgress
    from media_hygiene.services.import_run import ImportService
    from media_hygiene.services.interrupt import StopRequest
    from media_hygiene.services.next_command import CHANGING, NextVerb

    sources = [folder] if folder else backup
    runtime = runtime_of(ctx).with_overrides(folder_options.backup_layer(sources))
    output = runtime.output
    with user_errors(output):
        ImportService(runtime, NullProgress()).ensure_ready()
        with RichProgress(output.console) as progress:
            plan = ImportService(runtime, progress).prepare(
                runtime.mapper.to_container(to) if to else None
            )
    show_plan(runtime, plan)
    if not plan.jobs:
        output.success(_("Nothing to import: every file of the folder is dealt with."))
        return
    if not yes and not typer.confirm(_("Copy them into your photos?"), default=True):
        raise typer.Exit
    output.info(
        _(
            "🛟 The folder is only read: each file is copied, compared with its "
            "source, journaled; 'undo' removes the copies."
        )
    )
    with RichProgress(output.console) as progress, StopRequest() as stop:
        result = ImportService(runtime, progress).execute(plan, stop.requested)
    show_result(runtime, result)
    safety(
        runtime,
        _(
            "Changed your mind? 'media-hygiene undo {run_id}' removes the copies:"
        ).format(run_id=result.run_id),
        NextVerb(carried(runtime, f"undo {result.run_id}"), CHANGING),
    )
    suggest(
        runtime,
        _("audit again: the new photos join your library."),
        NextVerb(carried(runtime, "audit")),
    )
