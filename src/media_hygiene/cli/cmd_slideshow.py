"""`media-hygiene slideshow`: photos on the TV, the phone choosing the next (0291)."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import review_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _, ngettext


# The options are parameters: the documented exception for Typer commands.
def slideshow_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    folder: Annotated[
        str | None,
        typer.Option(
            "--folder",
            help=_(
                "Show the photos of this folder and its subfolders, as the Explorer "
                'shows it: "C:\\Photos\\2026 Holidays".'
            ),
            show_default=False,
        ),
    ] = None,
    words: Annotated[
        str | None,
        typer.Option(
            "--search",
            help=_('Show the photos a search finds, as typed in search: "noel 2025".'),
            show_default=False,
        ),
    ] = None,
    chosen: Annotated[
        bool,
        typer.Option(
            "--chosen",
            help=_("Show the files set aside in search or browse."),
        ),
    ] = False,
    port: Annotated[int | None, review_options.port()] = None,
) -> None:
    """Show photos on the TV, the phone choosing the next one, until Ctrl+C.

    Args:
        ctx: Typer context holding the runtime.
        folder: `--folder`, a folder as the Explorer shows it.
        words: `--search`, the words of a search.
        chosen: `--chosen`, the files set aside.
        port: `--port`, inside the container.
    """
    from media_hygiene.services.slideshow import ShowStart, serve_slideshow
    from media_hygiene.services.slideshow_pick import Pick

    runtime = runtime_of(ctx)
    port = review_options.page_port(runtime, port)
    pick = Pick(folder=folder, words=words, chosen=chosen)
    with user_errors(runtime.output):
        shown = serve_slideshow(runtime, ShowStart(pick, port))
    runtime.output.blank()
    runtime.output.success(
        ngettext(
            "Slideshow over ({n} photo); your photos were not changed.",
            "Slideshow over ({n} photos); your photos were not changed.",
            shown,
        ).format(n=shown)
    )
