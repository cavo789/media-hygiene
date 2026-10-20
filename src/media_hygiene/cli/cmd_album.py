"""`media-hygiene album`: gather a selection into a folder of hard links."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Final

import typer

from media_hygiene.cli import folder_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.options import panel_advanced
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.services.album import AlbumPrepared
    from media_hygiene.services.runtime import Runtime

_MOST_STARS: Final = 5


# The options are parameters: the documented exception for Typer commands.
def album_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    name: Annotated[
        str,
        typer.Argument(help=_("The album's name: the folder holding its links.")),
    ],
    *,
    category: Annotated[
        str,
        typer.Option(
            "--category",
            help=_("The files of this category, as the edited workbook says."),
        ),
    ] = "",
    event: Annotated[
        str,
        typer.Option("--event", help=_("The files of this event: its id or its name.")),
    ] = "",
    rule: Annotated[
        str,
        typer.Option(
            "--rule",
            rich_help_panel=panel_advanced(),
            help=_("The files the classify rule of this name decided."),
        ),
    ] = "",
    rating: Annotated[
        int | None,
        typer.Option(
            "--rating",
            rich_help_panel=panel_advanced(),
            min=1,
            max=_MOST_STARS,
            help=_("The files given at least these stars in Windows (1 to 5)."),
        ),
    ] = None,
    workbook: Annotated[
        str | None,
        typer.Option(
            "--workbook",
            rich_help_panel=panel_advanced(),
            help=_(
                "The classify workbook to read; the latest classify run's by default."
            ),
        ),
    ] = None,
    apply: Annotated[
        bool,
        typer.Option(
            "--apply",
            help=_("Make the links; without it, only show what the album gathers."),
        ),
    ] = False,
    backup: Annotated[list[str] | None, folder_options.kept_backup()] = None,
) -> None:
    """Show what the album gathers; with --apply, make one hard link per file.

    Args:
        ctx: Typer context holding the runtime.
        backup: `--backup` folders, read-only on purpose: never refused (0262).
        name: The album's name.
        category: `--category`.
        event: `--event`.
        rule: `--rule`.
        rating: `--rating`, the fewest stars; None when not asked.
        workbook: `--workbook`, or None for the latest.
        apply: `--apply`, make the links.
    """
    from media_hygiene.classify.album_rows import Criteria
    from media_hygiene.console.album_view import show_album
    from media_hygiene.scan.progress import NullProgress
    from media_hygiene.services.album import AlbumRequest, AlbumService

    runtime = runtime_of(ctx).with_overrides(folder_options.backup_layer(backup))
    request = AlbumRequest(name, Criteria(category, event, rule, rating or 0), workbook)
    with user_errors(runtime.output):
        service = AlbumService(runtime, NullProgress())
        service.ensure_ready()
        prepared = service.prepare(request)
    runtime.output.title(_("Album {name}").format(name=name.strip()))
    show_album(runtime, prepared)
    if apply:
        _make(runtime, prepared)
    else:
        runtime.output.tip(_("Nothing was changed: add --apply to make the links."))


def _make(runtime: Runtime, prepared: AlbumPrepared) -> None:
    """Make the links, then say what was made and how to undo it.

    Args:
        runtime: Settings, mount points and output.
        prepared: The album.
    """
    from media_hygiene.cli.next_steps import carried, safety
    from media_hygiene.console.album_view import show_album_result
    from media_hygiene.console.progress import RichProgress
    from media_hygiene.services.album import AlbumService
    from media_hygiene.services.interrupt import StopRequest
    from media_hygiene.services.next_command import CHANGING, NextVerb

    output = runtime.output
    if not prepared.plan.links:
        output.success(_("Nothing to add: the album holds every file found."))
        return
    output.info(
        _(
            "🛟 An album only adds names (hard links): no photo is copied, moved nor "
            "deleted, and 'undo' removes it."
        )
    )
    with RichProgress(output.console) as progress, StopRequest() as stop:
        result = AlbumService(runtime, progress).execute(prepared, stop.requested)
    show_album_result(runtime, result)
    safety(
        runtime,
        _(
            "'media-hygiene undo {run_id}' removes the album; the photos stay "
            "where they are:"
        ).format(run_id=result.run_id),
        NextVerb(carried(runtime, f"undo {result.run_id}"), CHANGING),
    )
