"""`media-hygiene browse`: walk through the folders in the browser, set photos aside."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from functools import partial
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

    Raises:
        Exit: With `100 + n` when *Apply now* chose step `n` (opened from the home
            page): `mh` runs it, then opens the home page again.
    """
    from media_hygiene.cli.browse_apply import apply_step
    from media_hygiene.cli.cmd_search import suggest_clean
    from media_hygiene.services.home import launcher_relays_steps
    from media_hygiene.services.search import BrowseStart, open_search, serve_browse

    runtime = runtime_of(ctx)
    output = runtime.output
    # Opened from the home page: `mh` runs the step *Apply now* ends on (0243).
    apply = partial(apply_step, runtime) if launcher_relays_steps() else None
    with user_errors(output), open_search(runtime, words=False) as search:
        served = serve_browse(runtime, search, BrowseStart(port, apply))
        output.blank()
        output.success(_("Folders closed; your photos were not changed."))
        step = apply_step(runtime) if served.code else None
        if step is not None:
            said = _("Apply now, chosen on the page: {command}")
            output.info(said.format(command=step.command))
            raise typer.Exit(served.code)
        if served.chosen:
            suggest_clean(runtime, served.chosen)
