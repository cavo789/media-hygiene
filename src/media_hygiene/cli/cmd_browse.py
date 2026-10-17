"""`media-hygiene browse`: walk through the folders in the browser, set photos aside."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import review_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _


def browse_command(
    ctx: typer.Context,
    *,
    port: Annotated[int, review_options.port()] = review_options.PAGE_PORT,
) -> None:
    """Walk through the folders of the library, as in Explorer, until Ctrl+C.

    Args:
        ctx: Typer context holding the runtime.
        port: `--port`, inside the container.
    """
    from media_hygiene.cli.cmd_search import suggest_clean
    from media_hygiene.services.search import open_search, serve_browse

    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output), open_search(runtime, words=False) as search:
        chosen = serve_browse(runtime, search, port)
        output.blank()
        output.success(_("Folders closed; your photos were not changed."))
        if chosen:
            suggest_clean(runtime, chosen)
