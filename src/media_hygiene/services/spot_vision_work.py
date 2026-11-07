"""🤖 Which photos `spots --vision` asks about, and the landmarks offered for each."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.errors import GeoDataError
from media_hygiene.geo.distance import Point
from media_hygiene.geo.landmarks import near_cells, shared_landmarks
from media_hygiene.index.spot_picks import Unpicked, unpicked
from media_hygiene.scan.filters import media_kind
from media_hygiene.services.chosen_place import chosen_store

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.services.runtime import Runtime

# How far a landmark a photo shows may lie: a cathedral seen from across a town.
PICK_M: Final = 1000.0
# The nearest ones only: a long list slows the model and invites a wrong pick.
MAX_CANDIDATES: Final = 10

type Work = tuple[Unpicked, tuple[str, ...]]


def landmark_work(runtime: Runtime, connection: sqlite3.Connection) -> list[Work]:
    """The pictures the model would be asked about, and the landmarks around each.

    A video is not shown to the model, a file set aside counts as gone.

    Args:
        runtime: Where the set-aside files are listed.
        connection: The index.

    Returns:
        Each photo with at least one landmark around, nearest first.
    """
    aside = chosen_store(runtime).paths()
    to_host = runtime.mapper.to_host
    photos = [
        photo
        for photo in unpicked(connection)
        if media_kind(Path(photo.path)) is MediaKind.IMAGE
        and to_host(Path(photo.path)) not in aside
    ]
    if not photos:
        return []
    points = [Point(photo.latitude, photo.longitude) for photo in photos]
    try:
        landmarks = shared_landmarks(near_cells(points))
    except GeoDataError:
        return []
    found = (
        (photo, landmarks.around(point, PICK_M)[:MAX_CANDIDATES])
        for photo, point in zip(photos, points, strict=True)
    )
    return [(photo, names) for photo, names in found if names]
