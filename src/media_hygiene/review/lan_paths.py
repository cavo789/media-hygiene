"""What a paired phone may ask of the home server under `mh --lan` (0269, 0360).

An explicit list, every other path refused (`lan_app`): the home page's reads, the
audit's progress (never its start: an audit follows a change made on the PC, 0427),
the albums (0297), and `search`/`browse` served by the home server (0356) with their
pictures, and the presence (0416: an open phone keeps the server up). Their
searches and folder lists are `POST` but change nothing; what
writes (*set aside*, *Apply now*, a move, a rule, a name refused) stays the PC's
(`write_routes`, 0429: whatever the settings). `[review] lan_phone_originals` adds the
originals (`/original/`), a read (0427).
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Final

from media_hygiene.docs.pages import DOCS_PREFIX
from media_hygiene.review.home_app import AUDIT_PATH
from media_hygiene.review.home_assets import ASSETS_PREFIX, FAVICON_PATH
from media_hygiene.review.home_views import REPORTS_PREFIX
from media_hygiene.review.http import ContentType
from media_hygiene.review.local_app import PAGE_PATH, STATE_PATH
from media_hygiene.review.presence import PRESENCE_PATH
from media_hygiene.review.videos import VIDEO_PREFIX
from media_hygiene.search.app import SEARCH_PAGE_PATH, SEARCH_PATH
from media_hygiene.search.chosen_api import CHOSEN_PATH
from media_hygiene.search.folders import BROWSE_PATH, FOLDER_POSTS, FOLDERS_PATH
from media_hygiene.search.views import ORIGINAL_PREFIX, PREVIEW_PREFIX, THUMB_PREFIX
from media_hygiene.share import album_page as albums

if TYPE_CHECKING:
    from media_hygiene.review.http import Request, Response

_HOME_READS: Final = frozenset({PAGE_PATH, STATE_PATH, AUDIT_PATH, FAVICON_PATH})
_SEARCH_READS: Final = frozenset({SEARCH_PAGE_PATH, BROWSE_PATH, FOLDERS_PATH})
READ_PATHS: Final = _HOME_READS | _SEARCH_READS | {CHOSEN_PATH} | albums.PHONE_READS
_HOME_PREFIXES: Final = (REPORTS_PREFIX, ASSETS_PREFIX, DOCS_PREFIX)
# A photo opens at its preview size: never an original over the Wi-Fi.
_SEARCH_PREFIXES: Final = (THUMB_PREFIX, PREVIEW_PREFIX, VIDEO_PREFIX)
READ_PREFIXES: Final = (
    *_HOME_PREFIXES,
    *_SEARCH_PREFIXES,
    *albums.PHONE_READ_PREFIXES,
)
# `POST /api/alive`: an open phone keeps the PC's server up (0416).
_SAYS: Final = frozenset({SEARCH_PATH, PRESENCE_PATH})
# The `POST`s a phone may send: reads, but an album's change (0295: never a photo's).
# No album change from a phone: albums are made on the PC (0435, decided 2026-10-27).
POST_PATHS: Final = _SAYS | FOLDER_POSTS
# The one acting step a paired phone may start on the PC (0444, maintainer 2026-10-28):
# an album saved on the PC, on the TV (`lan_show`). Every other step stays the PC's.
PHONE_STEPS: Final = frozenset({"slideshow-album"})
# The steps a phone opens as pages instead of asking the PC to run them.
PHONE_PAGES: Final = {"mh search": SEARCH_PAGE_PATH, "mh browse": BROWSE_PATH}
_GET, _POST = "GET", "POST"
# The controls of a page of photos to pick that write, hidden on a phone (0429).
PHONE_HIDDEN: Final = (
    "#setAside", "#takeBack", "#chosen", "#applyBar", "#ruleOpen", "#moveBar",
    ".unname", ".writes",
    # Nothing to pick on a phone, no keyboard, albums made on the PC (2026-10-27).
    "#albumBar", "#keys", ".tick",
)  # fmt: skip


def phone_may(request: Request, *, originals: bool = False) -> bool:
    """Tell whether a paired phone may ask this.

    Args:
        request: The request.
        originals: `[review] lan_phone_originals`: the originals may be downloaded.

    Returns:
        True for a listed read (`GET`) or a listed `POST`.
    """
    path = request.path
    if request.method == _GET:
        if originals and path.startswith(ORIGINAL_PREFIX):
            return True
        return path in READ_PATHS or path.startswith(READ_PREFIXES)
    return request.method == _POST and path in POST_PATHS


def phone_marked(response: Response) -> Response:
    """Mark a page sent to a phone: its controls that write are hidden (0429).

    Args:
        response: What the home page answered.

    Returns:
        The page with `<html data-phone …>`; anything else as it was.
    """
    if response.content_type is not ContentType.HTML:
        return response
    body = response.body.replace(b"<html ", b"<html data-phone ", 1)
    return replace(response, body=body)
