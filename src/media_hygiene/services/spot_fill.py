"""Fill the index with where each located photo lies: offline, once per position (0545).

Run by every `audit`, and by `spots` for the photos already indexed. Nothing leaves the
machine: GeoNames is read from the image; the OpenStreetMap names are those already kept
in the cache after the user's Yes (`services.place_names`), so a Yes given later reaches
the rows at the next run. The user's own places are not stored: they live in
`config.toml` and are read at each show (`search.spot_label`), a place drawn today
applies at once.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import GeoDataError
from media_hygiene.geo.distance import Point
from media_hygiene.geo.gazetteer import GEO_DATA, TOWNS_FILE
from media_hygiene.geo.landmarks import LANDMARKS_FILE, near_cells, shared_landmarks
from media_hygiene.geo.reverse import rounded
from media_hygiene.geo.towns_once import shared_towns
from media_hygiene.i18n import _
from media_hygiene.index.spot_rows import (
    Known,
    SpotSource,
    forget_unlocated,
    located_files,
    save_spots,
)
from media_hygiene.scan.progress import Step
from media_hygiene.services.place_names import read_names, spot_key
from media_hygiene.services.spot_namer import SpotNamer
from media_hygiene.services.spot_sidecars import as_named, sidecar_names, unrejected

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Mapping

    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime

_FORMAT: Final = 1  # of a row; a change of it refills every row
_BATCH: Final = 500  # rows between two commits: a stop keeps what is done
_DIGITS: Final = 16


def _stamp(runtime: Runtime) -> str:
    """Name what a row is worked out from, besides the position.

    Args:
        runtime: Settings: the words searched depend on them.

    Returns:
        A digest of the snapshot's towns file size, `[tags] town_km` and the user's
        names of towns: any change refills the rows.
    """
    settings = runtime.settings
    said = (
        _FORMAT,
        _snapshot_mark(),
        settings.tags.town_km,
        sorted(settings.classify.town_names.items()),
    )
    text = json.dumps(said)
    return hashlib.sha256(text.encode()).hexdigest()[:_DIGITS]


def _snapshot_mark() -> int:
    """Tell one snapshot from another, without reading it.

    Returns:
        The size of its towns and landmarks files: `geonames_update` changes them.
    """
    files = (GEO_DATA / TOWNS_FILE, GEO_DATA / LANDMARKS_FILE)
    return sum(path.stat().st_size for path in files if path.exists())


def _stale(known: Known, stamp: str, online: Mapping[str, str]) -> bool:
    """Tell whether a file's row must be written again.

    Args:
        known: The file and its row.
        stamp: The stamp of this run.
        online: The OpenStreetMap names kept.

    Returns:
        True for no row, another position or stamp, or an online name it lacks.
    """
    if known.stored_at != (known.latitude, known.longitude) or known.stamp != stamp:
        return True
    if known.source in {SpotSource.USER, SpotSource.VISION}:
        return False
    key = spot_key(rounded(Point(known.latitude, known.longitude)))
    name = online.get(key, "")
    return bool(name) and name != known.landmark


def fill_spots(
    runtime: Runtime, connection: sqlite3.Connection, progress: ProgressSink
) -> int:
    """Write the rows missing or out of date; the snapshot is read only if there are.

    Args:
        runtime: Settings and the cache folder.
        connection: The index, open for writing.
        progress: Where the progress line goes.

    Returns:
        How many rows were written.
    """
    forget_unlocated(connection)
    stamp = _stamp(runtime)
    online = read_names(runtime.locations.cache_dir)
    stale = [
        known for known in located_files(connection) if _stale(known, stamp, online)
    ]
    if not stale:
        return 0
    progress.start(
        Step(
            _("Naming where the photos were taken"),
            _("Their landmark, town and regions, offline: nothing leaves this PC."),
        ),
        len(stale),
    )
    try:
        points = (Point(known.latitude, known.longitude) for known in stale)
        landmarks = shared_landmarks(near_cells(points))
        namer = SpotNamer(runtime, (shared_towns(), landmarks, online), stamp)
    except GeoDataError:
        progress.stop()
        return 0
    said = sidecar_names(stale)  # the truth, before the cache (0649)
    rows: list[tuple[object, ...]] = []
    for known in stale:
        rows.append(unrejected(namer.row(as_named(known, said)), said))
        progress.advance()
        if len(rows) >= _BATCH:
            save_spots(connection, rows)
            rows.clear()
    save_spots(connection, rows)
    progress.stop()
    return len(stale)
