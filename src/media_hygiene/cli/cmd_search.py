"""`media-hygiene search`: find photos by their words, in the browser or the console."""

from __future__ import annotations

from typing import Annotated, Final

import typer

from media_hygiene.cli import review_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.next_steps import carried, suggest
from media_hygiene.i18n import _
from media_hygiene.services.next_command import NextVerb
from media_hygiene.services.search import (
    Printed,
    open_search,
    print_found,
    serve_search,
)

_PRINTED: Final = 20


# The options are parameters: the documented exception for Typer commands.
def search_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    words: Annotated[
        list[str] | None,
        typer.Argument(
            help=_(
                "Words to find, printed as a table instead of opening the page: "
                '"bord de mer" a phrase, anniv* a start of word, place:durbuy '
                "among the places only (also vision, caption, folder, date, person)."
            ),
            show_default=False,
        ),
    ] = None,
    *,
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            min=1,
            help=_("How many files the table lists at most. Default: {count}.").format(
                count=_PRINTED
            ),
            show_default=False,
        ),
    ] = _PRINTED,
    port: Annotated[int, review_options.port()] = review_options.PAGE_PORT,
) -> None:
    """Search the words of the photos: the page until Ctrl+C, or a table.

    Args:
        ctx: Typer context holding the runtime.
        words: The words; none serves the page.
        limit: `--limit`, rows of the table.
        port: `--port`, inside the container.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output), open_search(runtime) as search:
        if words:
            if print_found(runtime, search, Printed(" ".join(words), limit)):
                suggest(
                    runtime,
                    _(
                        "the same search in your browser, with the pictures and "
                        "filters."
                    ),
                    NextVerb(carried(runtime, "search"), port=port),
                )
            return
        serve_search(runtime, search, port)
        output.blank()
        output.success(_("Search stopped; nothing was changed."))
