"""The files picked on a page of tiles, shown on the TV by the home server (0454).

📺 *On the TV*, in the bar of `library` and `browse`, sends the files picked (or every
file the page shows) through the page's albums API (`action: "tv"`): the page's own
picker turns its keys into files of the index, never a path from the request, and
caps them as an album (`MAX_ADDED`). The home server's slideshow (`slideshow_here`)
then shows them in place of the show running. The page and the slideshow are built
apart, so this slot joins them: the slideshow fills it when the home server starts.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.review.album_show import SLIDESHOW_PAGE
from media_hygiene.review.serving import json_response
from media_hygiene.services.slideshow_pick import Pick
from media_hygiene.slideshow.tv_door import SCREEN_PATH

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.http import Response
    from media_hygiene.review.lan_phones import PhoneBook
    from media_hygiene.slideshow.screens import Screens

# The screen in a tab of this PC (0659): paired at once, the keyboard as its remote.
HERE_SCREEN: Final = f"{SLIDESHOW_PAGE}{SCREEN_PATH.removeprefix('/')}?here=1"


@dataclass(slots=True)
class TvSlot:
    """Where a page sends its files to the TV; empty until a slideshow listens."""

    start: Callable[[tuple[Path, ...]], Response] | None = None
    known: Callable[[], bool] | None = None  # a TV to show on: the cards' 📺 (0523)

    def paired(self) -> bool:
        """Tell whether a TV is paired, for the pages' 📺.

        Returns:
            False while no slideshow listens.
        """
        return self.known is not None and self.known()

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


def any_tv(screens: Screens, phones: PhoneBook | None) -> bool:
    """Tell whether a TV is paired: in this run, or kept for good (0456).

    A TV kept for good joins `screens` only at its next visit: its file says it first.

    Args:
        screens: The TVs of this run.
        phones: The phones' book, whose `tvs.json` keeps them; None: in memory only.

    Returns:
        True when the page may offer "on the TV".
    """
    return screens.paired > 0 or (phones is not None and bool(phones.tvs().listed()))


def selected(
    begin: Callable[[Pick], bool], files: tuple[Path, ...], *, ordered: bool = False
) -> Response:
    """Show the files picked on a page, in place of the show running.

    Args:
        begin: Starts a show; True when it replaced one.
        files: The files, in the container, read from the index.
        ordered: True to keep the files' order (a random show), else oldest first.

    Returns:
        The remote's page, the screen's on this PC (0659: full screen, the keyboard
        as remote) and whether a show was replaced; 409 with the reason.
    """
    try:
        replaced = begin(Pick(files=files, ordered=ordered))
    except MediaHygieneError as exc:
        return json_response(HTTPStatus.CONFLICT, {"error": why(exc)})
    return json_response(
        HTTPStatus.OK,
        {"page": SLIDESHOW_PAGE, "screen": HERE_SCREEN, "replaced": replaced},
    )


def why(error: MediaHygieneError) -> str:
    """The reason nothing is shown, and its tip.

    Args:
        error: Why.

    Returns:
        The text.
    """
    return str(error) if error.tip is None else f"{error}\n{error.tip}"
