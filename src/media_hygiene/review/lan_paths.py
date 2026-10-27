"""What a paired phone may ask of the home server under `mh --lan` (0269, 0360).

An explicit list, every other path refused (`lan_app`): the home page's reads, the
audit, the albums (0297), and `search`/`browse` served by the home server (0356) with
their pictures, and the presence (0416: an open phone keeps the server up). Their
searches and folder lists are `POST` but change nothing; what
writes (*set aside*, *Apply now*, a move, a rule, a name refused) stays the PC's.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.docs.pages import DOCS_PREFIX
from media_hygiene.review.home_app import AUDIT_PATH
from media_hygiene.review.home_assets import ASSETS_PREFIX, FAVICON_PATH
from media_hygiene.review.home_views import REPORTS_PREFIX
from media_hygiene.review.local_app import PAGE_PATH, STATE_PATH
from media_hygiene.review.presence import PRESENCE_PATH
from media_hygiene.review.videos import VIDEO_PREFIX
from media_hygiene.search.app import SEARCH_PAGE_PATH, SEARCH_PATH
from media_hygiene.search.chosen_api import CHOSEN_PATH
from media_hygiene.search.folders import BROWSE_PATH, FOLDER_POSTS, FOLDERS_PATH
from media_hygiene.search.views import PREVIEW_PREFIX, THUMB_PREFIX
from media_hygiene.share import album_page as albums

if TYPE_CHECKING:
    from media_hygiene.review.http import Request

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
_SAYS: Final = frozenset({AUDIT_PATH, SEARCH_PATH, PRESENCE_PATH})
WRITE_PATHS: Final = albums.PHONE_WRITES | _SAYS | FOLDER_POSTS
# The steps a phone opens as pages instead of asking the PC to run them.
PHONE_PAGES: Final = {"mh search": SEARCH_PAGE_PATH, "mh browse": BROWSE_PATH}
_GET, _POST = "GET", "POST"


def phone_may(request: Request) -> bool:
    """Tell whether a paired phone may ask this.

    Args:
        request: The request.

    Returns:
        True for a listed read (`GET`) or a listed `POST`.
    """
    path = request.path
    if request.method == _GET:
        return path in READ_PATHS or path.startswith(READ_PREFIXES)
    return request.method == _POST and path in WRITE_PATHS
