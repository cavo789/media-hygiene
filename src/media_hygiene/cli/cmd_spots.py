"""`media-hygiene spots`: name where the photos already indexed were taken (0545)."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _


def spots_command(ctx: typer.Context) -> None:
    """Name where the photos of the index were taken, offline, and read it back.

    Args:
        ctx: Typer context holding the runtime.
    """
    from media_hygiene.console.progress import RichProgress
    from media_hygiene.services.spot_scan import scan_spots

    runtime = runtime_of(ctx)
    output = runtime.output
    output.info(_("🔒 Your photos are not read: only the index, offline."))
    with user_errors(output), RichProgress(output.console) as progress:
        scan = scan_spots(runtime, progress)
    output.success(
        _(
            "{stored} photos located, {landmarks} at a landmark, {towns} near a town "
            "({written} just named). Read back from the index."
        ).format(
            stored=scan.figures.stored,
            landmarks=scan.figures.landmarks,
            towns=scan.figures.towns,
            written=scan.written,
        )
    )
    output.next_step(_("find them by a monument or a town: mh library."))
