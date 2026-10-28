"""The files picked on a page of tiles, shown on the TV by the home server (0454).

📺 *On the TV*, in the bar of `search` and `browse`, sends the files picked (or every
file the page shows) through the page's albums API (`action: "tv"`): the page's own
picker turns its keys into files of the index, never a path from the request, and
caps them as an album (`MAX_ADDED`). The home server's slideshow (`slideshow_here`)
then shows them in place of the show running. The page and the slideshow are built
apart, so this slot joins them: the slideshow fills it when the home server starts.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.review.album_show import SLIDESHOW_PAGE
from media_hygiene.review.serving import json_response
from media_hygiene.services.slideshow_pick import Pick

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.http import Response


@dataclass(slots=True)
class TvSlot:
    """Where a page sends its files to the TV; empty until a slideshow listens."""

    start: Callable[[tuple[Path, ...]], Response] | None = None

    def __call__(self, files: tuple[Path, ...]) -> Response:
        """Show the files on the TV, in place of the show running.

        Args:
            files: The files, in the container, read from the index.

        Returns:
            The slideshow's answer; 404 while no slideshow listens.
        """
        if self.start is None:
            message = _("Open this page from the home page to show it on the TV.")
            return json_response(HTTPStatus.NOT_FOUND, {"error": message})
        return self.start(files)


def selected(begin: Callable[[Pick], bool], files: tuple[Path, ...]) -> Response:
    """Show the files picked on a page, in place of the show running.

    Args:
        begin: Starts a show; True when it replaced one.
        files: The files, in the container, read from the index.

    Returns:
        The remote's page and whether a show was replaced; 409 with the reason.
    """
    try:
        replaced = begin(Pick(files=files))
    except MediaHygieneError as exc:
        return json_response(HTTPStatus.CONFLICT, {"error": why(exc)})
    return json_response(HTTPStatus.OK, {"page": SLIDESHOW_PAGE, "replaced": replaced})


def why(error: MediaHygieneError) -> str:
    """The reason nothing is shown, and its tip.

    Args:
        error: Why.

    Returns:
        The text.
    """
    return str(error) if error.tip is None else f"{error}\n{error.tip}"
