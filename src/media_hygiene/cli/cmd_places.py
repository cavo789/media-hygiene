"""`media-hygiene places`: name your places on a map, saved into `config.toml`."""

from __future__ import annotations

from typing import Annotated, Final

import typer

from media_hygiene.cli import review_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _
from media_hygiene.services.places import open_places, serve_places

PLACES_PORT: Final = 8080


def places_command(
    ctx: typer.Context,
    *,
    port: Annotated[int, review_options.port()] = PLACES_PORT,
) -> None:
    """Serve the map of the photos' positions until Ctrl+C.

    Args:
        ctx: Typer context holding the runtime.
        port: `--port`, inside the container.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        board = open_places(runtime)
        serve_places(runtime, board, port)
        output.blank()
        output.success(_("Map stopped; your places are in config.toml."))
        output.tip(
            _(
                "Next: a 'place' rule (and a 'trip' rule) in [[classify.rules]], "
                "then 'classify'."
            )
        )
