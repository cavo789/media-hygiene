"""`media-hygiene xmp`: write the tags into `.xmp` sidecars, journaled and undoable."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import folder_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _


def xmp_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    path: Annotated[
        list[str] | None,
        typer.Option(
            "--path",
            help=_(
                "Only the photos below this folder (host path, as you mounted it); "
                "repeat it for several. Default: every file of the index."
            ),
            show_default=False,
        ),
    ] = None,
    apply: Annotated[
        bool,
        typer.Option(
            "--apply",
            help=_("Write the sidecars; without it, only show what would be written."),
        ),
    ] = False,
    backup: Annotated[list[str] | None, folder_options.kept_backup()] = None,
) -> None:
    """Show the sidecars to write; with --apply, write them, journaled.

    Args:
        ctx: Typer context holding the runtime.
        backup: `--backup` folders, read-only on purpose: never refused (0262).
        path: `--path`, host folders.
        apply: `--apply`, write the sidecars.
    """
    from media_hygiene.cli.next_steps import carried, safety
    from media_hygiene.console.progress import RichProgress
    from media_hygiene.console.xmp_view import show_plan, show_result
    from media_hygiene.scan.progress import NullProgress
    from media_hygiene.services.interrupt import StopRequest
    from media_hygiene.services.next_command import CHANGING, NextVerb
    from media_hygiene.services.xmp import XmpService

    runtime = runtime_of(ctx).with_overrides(folder_options.backup_layer(backup))
    output = runtime.output
    within = tuple(runtime.mapper.to_container(folder) for folder in path or ())
    with user_errors(output):
        service = XmpService(runtime, NullProgress())
        service.ensure_ready(apply=apply)
        plan = service.prepare(within)
    show_plan(runtime, plan)
    if not apply:
        output.tip(_("Nothing was changed: add --apply to write the sidecars."))
        return
    if not plan.jobs:
        output.success(_("Nothing to write."))
        return
    output.info(
        _(
            "🛟 Only .xmp sidecars are written, never a photo: each one is journaled "
            "and 'undo' takes it back."
        )
    )
    with RichProgress(output.console) as progress, StopRequest() as stop:
        result = XmpService(runtime, progress).execute(plan, stop.requested)
    show_result(runtime, result)
    safety(
        runtime,
        _(
            "Changed your mind? 'media-hygiene undo {run_id}' removes the sidecars "
            "written and puts the others back as they were:"
        ).format(run_id=result.run_id),
        NextVerb(carried(runtime, f"undo {result.run_id}"), CHANGING),
    )
