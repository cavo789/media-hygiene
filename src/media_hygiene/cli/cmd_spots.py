"""`media-hygiene spots`: name where the photos already indexed were taken (0545).

With `--vision` (🤖, 0589), a local model then picks the landmark each photo shows.
"""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer
from rich.markup import escape

from media_hygiene.cli import options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def spots_command(
    ctx: typer.Context,
    *,
    vision: Annotated[
        bool,
        typer.Option(
            "--vision",
            help=escape(
                _(
                    "🤖 Then let the local vision model of [classify.ai] pick, "
                    "among the landmarks within 1 km, the one each photo shows "
                    "(sends the photos to that model only; "
                    "a name typed by hand always wins)."
                )
            ),
            rich_help_panel=options.panel_local_ai(),
        ),
    ] = False,
) -> None:
    """Name where the photos of the index were taken, offline, and read it back.

    Args:
        ctx: Typer context holding the runtime.
        vision: Also ask the local vision model which landmark each photo shows.
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
    if vision:
        _vision(runtime)
    output.next_step(_("find them by a monument or a town: mh library."))


def _vision(runtime: Runtime) -> None:
    """Let the local model pick the landmark each photo shows, and say how it went.

    Args:
        runtime: The runtime.
    """
    from media_hygiene.console.progress import RichProgress
    from media_hygiene.services.spot_vision import pick_landmarks

    output = runtime.output
    output.info(
        _("🤖 Your photos are shown to your local model only: nothing is moved.")
    )
    with user_errors(output), RichProgress(output.console) as progress:
        picks = pick_landmarks(runtime, progress)
    output.success(
        _(
            "🤖 {asked} photos shown to the model: {picked} landmarks picked, "
            "{none} showing none, {unclear} unclear (left as they were)."
        ).format(
            asked=picks.asked,
            picked=picks.picked,
            none=picks.none,
            unclear=picks.unclear,
        )
    )
