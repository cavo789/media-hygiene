"""The random photos of the home page (0485): drawn from the index, each visit.

`GET /api/samples` runs once per page load, never with the state: the page polls that.
Read only: thumbnails from `library`'s routes and preview cache. A broken file, a video,
a file set aside (it counts as gone) or one no longer on the disk is skipped.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING, Final
from urllib.parse import urlencode

from media_hygiene.constants import MediaKind
from media_hygiene.index.read_only import connect_read_only
from media_hygiene.review.home_parts import HomeSample
from media_hygiene.scan.filters import media_kind
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.search.folders import FOLDER_QUERY
from media_hygiene.search.views import JPEG, THUMB_PREFIX
from media_hygiene.services.chosen_place import chosen_store

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

SAMPLES: Final = 10
_DRAWN: Final = SAMPLES * 6  # more than shown: videos and files gone are skipped
_DRAW: Final = (
    "SELECT rowid, path FROM files WHERE broken_reason IS NULL "
    "ORDER BY RANDOM() LIMIT ?"
)


def home_samples(runtime: Runtime) -> tuple[HomeSample, ...]:
    """Draw about ten readable photos from the index.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        At most `SAMPLES`; none without an index, or when it cannot be read.
    """
    index = runtime.index_file
    if index is None or not index.is_file():
        return ()
    try:
        with closing(connect_read_only(index)) as connection:
            rows = connection.execute(_DRAW, (_DRAWN,)).fetchall()
    except sqlite3.Error:
        return ()
    aside = chosen_store(runtime).paths()
    mapper = runtime.mapper
    samples: list[HomeSample] = []
    for key, text in rows:
        path = Path(text)
        host = mapper.to_host(path)
        if media_kind(path) is not MediaKind.IMAGE or host in aside:
            continue
        if not path.is_file():
            continue
        folder = mapper.to_host(path.parent)
        query = urlencode({FOLDER_QUERY: folder})
        samples.append(
            HomeSample(
                thumb=f"{THUMB_PREFIX}{key}{JPEG}",
                folder=folder,
                url=f"{SEARCH_PAGE_PATH}?{query}",
            )
        )
        if len(samples) == SAMPLES:
            break
    return tuple(samples)
