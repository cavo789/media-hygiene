"""A folder or a period on the TV, chosen on a paired phone (0455).

The phone's home page lists the folders the index holds (under the folders analysed)
and the months the audit read a date for; a tap starts the show in the home server,
through the path of 0454 (`slideshow_selection`): same cap, a running show replaced.
Read-only: the phone only shows. A folder is one of those listed, matched as text,
never a path from the request taken as is.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.i18n import _
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.serving import json_response
from media_hygiene.search import statements as sql
from media_hygiene.search.days import NAME as DAY
from media_hygiene.services.slideshow_selection import selected
from media_hygiene.share.album_api import too_many

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.http import Request
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.slideshow_pick import Pick

CHOICES_PATH: Final = "/choices"  # GET: the folders and the months
CHOOSE_PATH: Final = "/choose"  # POST: `{"folder": …}` or `{"first": …, "last": …}`
_AFTER_SLASH: Final = "0"  # the character after `/`: ends the range of a folder
_PATHS: Final = "SELECT path FROM files"
_MONTHS: Final = (
    f"SELECT DISTINCT substr({DAY}(media_date), 1, 7) AS month FROM files"  # noqa: S608
    " WHERE month IS NOT NULL ORDER BY month DESC"
)
_IN_DAYS: Final = f"SELECT path FROM files WHERE {sql.DAYS}"  # noqa: S608
_MAX_TEXT: Final = 4096


class Chosen(BaseModel):
    """What the phone asks: a folder as listed, or the first and last days."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    folder: str | None = None
    first: date | None = None
    last: date | None = None


@dataclass(frozen=True, slots=True)
class Chooser:
    """Answers the phone's choices; `opened` gives the settings and the open index."""

    opened: Callable[[], tuple[Runtime, SearchIndex]]
    begin: Callable[[Pick], bool]

    def answer(self, request: Request) -> Response | None:
        """Answer `/choices` and `/choose`; None for any other path.

        Args:
            request: The request, its path under `/slideshow`.

        Returns:
            The lists, the show started, or why not.
        """
        if request.method == "GET" and request.path == CHOICES_PATH:
            runtime, search = self.opened()
            listed = sorted(_folders(runtime, search), key=str.casefold)
            months = [row[0] for row in search.connection.execute(_MONTHS)]
            return json_response(HTTPStatus.OK, {"folders": listed, "months": months})
        if request.method != "POST" or request.path != CHOOSE_PATH:
            return None
        if not request.headers.get("content-type", "").startswith(ContentType.JSON):
            return Response(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        try:
            chosen = Chosen.model_validate(json.loads(request.body))
        except ValidationError, ValueError:
            return Response(HTTPStatus.BAD_REQUEST)
        return self._show(chosen)

    def _show(self, chosen: Chosen) -> Response:
        """Show a folder's files or a period's.

        Args:
            chosen: The folder, or the days.

        Returns:
            The remote's page; 409 with the reason when nothing is shown.
        """
        runtime, search = self.opened()
        if chosen.folder is not None:
            inside = _folders(runtime, search).get(chosen.folder[:_MAX_TEXT])
            if inside is None:
                return _refused(_("This folder is not among the folders analysed."))
            bounds = (f"{inside}/", f"{inside}{_AFTER_SLASH}")
            rows = search.connection.execute(sql.FOLDER_FILES, bounds)
            files = tuple(Path(row[1]) for row in rows)
        elif chosen.first is not None:
            days = (chosen.first.isoformat(), (chosen.last or chosen.first).isoformat())
            rows = search.connection.execute(_IN_DAYS, days)
            files = tuple(Path(row[0]) for row in rows)
            if not files:
                return _refused(_("No photo or video was taken in this period."))
        else:
            return Response(HTTPStatus.BAD_REQUEST)
        return too_many(files) or selected(self.begin, files)


def _folders(runtime: Runtime, search: SearchIndex) -> dict[str, Path]:
    """The folders holding files of the index, under the folders analysed.

    Args:
        runtime: Settings, mount points and the host mapper.
        search: The open index.

    Returns:
        By its name as the Explorer shows it, the folder in the container.
    """
    data = runtime.locations.data_dir
    mapper = runtime.mapper
    parents = {Path(row[0]).parent for row in search.connection.execute(_PATHS)}
    return {mapper.to_host(each): each for each in parents if each.is_relative_to(data)}


def _refused(message: str) -> Response:
    """Nothing shown, and why.

    Args:
        message: The reason.

    Returns:
        409 with it.
    """
    return json_response(HTTPStatus.CONFLICT, {"error": message})
