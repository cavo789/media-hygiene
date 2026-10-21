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
    port: Annotated[int | None, review_options.port()] = None,
) -> None:
    """Walk through the folders of the library, as in Explorer, until Ctrl+C.

    Args:
        ctx: Typer context holding the runtime.
        port: `--port`, inside the container.

    Raises:
        Exit: With `100 + n` when *Apply now* chose step `n` (opened from the home
            page): `mh` runs it, then opens the home page again.
    """
    from media_hygiene.cli.apply_step import end_on_applied, page_apply
    from media_hygiene.cli.cmd_search import suggest_clean
    from media_hygiene.services.search import BrowseStart, open_search, serve_browse

    runtime = runtime_of(ctx)
    port = review_options.page_port(runtime, port)
    output = runtime.output
    # Opened from the home page: `mh` runs the step *Apply now* ends on (0243).
    apply = page_apply(runtime)
    with user_errors(output), open_search(runtime, words=False) as search:
        served = serve_browse(runtime, search, BrowseStart(port, apply))
        output.blank()
        output.success(_("Folders closed; your photos were not changed."))
        end_on_applied(runtime, served.code)
        if served.chosen:
            suggest_clean(runtime, served.chosen)
