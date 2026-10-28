"""The towns read once per process: a server of the whole session reads them often.

The home server opens a slideshow per album and the map at each visit (0417); each read
of the snapshot takes 0.5 s and 90 MB at its peak, 36 MB kept (measured on the
devcontainer, demo tree).
"""

from __future__ import annotations

import functools

from media_hygiene.geo.gazetteer import Gazetteer


@functools.cache
def shared_towns() -> Gazetteer:
    """The towns of the snapshot, read at the first call only.

    Returns:
        The gazetteer; `renamed` gives the user's names without reading it again.
    """
    return Gazetteer.load()
