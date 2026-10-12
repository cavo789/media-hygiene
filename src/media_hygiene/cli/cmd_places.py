"""`media-hygiene places`: name your places on a map, saved into `config.toml`."""

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import review_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.next_steps import carried, suggest
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.next_command import NextVerb
from media_hygiene.services.places import open_places, serve_places


def places_command(
    ctx: typer.Context,
    *,
    port: Annotated[int, review_options.port()] = review_options.PAGE_PORT,
) -> None:
    """Serve the map of the photos' positions until Ctrl+C.

    Args:
        ctx: Typer context holding the runtime.
        port: `--port`, inside the container.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        again = NextVerb(
            carried(runtime, "places"),
            (MountKind.CONFIG, MountKind.CACHE),
            port=port,
        )
        board = open_places(runtime, again)
        serve_places(runtime, board, port)
        output.blank()
        output.success(_("Map stopped; your places are in config.toml."))
        suggest(
            runtime,
            _(
                "a 'place' rule (and a 'trip' rule) in [[classify.rules]], then "
                "'classify'."
            ),
            NextVerb(carried(runtime, "classify")),
        )
