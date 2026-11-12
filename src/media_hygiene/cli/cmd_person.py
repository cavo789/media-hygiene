"""`media-hygiene person PHOTO`: who is on this photo — name them, or set them aside."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import review_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _


def person_command(
    ctx: typer.Context,
    photo: Annotated[
        str,
        typer.Argument(
            help=_(
                "The photo, as the Explorer shows its path (C:\\Photos\\x.jpg), "
                "below the folders mounted."
            ),
            show_default=False,
        ),
    ],
    *,
    port: Annotated[int | None, review_options.port()] = None,
) -> None:
    """Open the page of one photo's faces: name each one, then confirm their photos.

    Args:
        ctx: Typer context holding the runtime.
        photo: The photo's path, host or container.
        port: `--port`, inside the container.

    Raises:
        Exit: With 2 when the path is not a photo of the folders mounted.
    """
    from media_hygiene.cli.cmd_search import suggest_clean
    from media_hygiene.person.finding import PhotoPlace
    from media_hygiene.services.search import SearchOpen, open_search, serve_person

    runtime = runtime_of(ctx)
    port = review_options.page_port(runtime, port)
    output = runtime.output
    place = PhotoPlace(runtime.mapper, runtime.locations.data_dir)
    if place.resolve(photo) is None:
        message = _("{path} is not a photo of the folders this page shows.")
        output.error(message.format(path=photo))
        raise typer.Exit(code=2)
    with user_errors(output), open_search(runtime) as search:
        chosen = serve_person(runtime, search, SearchOpen(port, photo))
        output.blank()
        output.success(_("Page stopped; your photos were not changed."))
        if chosen:
            suggest_clean(runtime, chosen)
