"""The landmarks of GeoNames, read offline: the monument a photo was taken at (0472).

The snapshot's `landmarks.tsv.xz` (see `ATTRIBUTION.txt`) lists monuments, castles,
churches, museums, towers… as GeoNames names and places them (classes S and L, the
codes of `tests/support/geonames/landmarks.py`). A photo is said to be at one when it
was taken within `NEAR_M` of it. No position ever leaves the machine. A snapshot
without the file (older) knows no landmark: the towns still answer.
"""

from __future__ import annotations

import functools
import lzma
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.geo.gazetteer import GEO_DATA
from media_hygiene.geo.nearest import NearestIndex

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.geo.distance import Point

LANDMARKS_FILE: Final = "landmarks.tsv.xz"
# How close a photo is taken to a landmark to be named after it: GeoNames places a
# landmark by one point (its centre, give or take), a phone's GPS errs by 5-50 m.
NEAR_M: Final = 200.0
_FIELDS: Final = 3  # name, latitude, longitude
_TAB: Final = "\t"
_M_PER_KM: Final = 1000.0


class Landmarks:
    """The landmarks of the snapshot, ready to answer."""

    __slots__ = ("_index", "_names")

    def __init__(self, names: tuple[str, ...], index: NearestIndex) -> None:
        """Keep the landmarks and their index.

        Args:
            names: Their names, by row.
            index: Their positions, same rows.
        """
        self._names = names
        self._index = index

    @classmethod
    def load(cls, folder: Path = GEO_DATA) -> Landmarks:
        """Read the landmarks of a snapshot; none when its file is missing or damaged.

        Args:
            folder: Where its files lie.

        Returns:
            The landmarks.
        """
        try:
            text = lzma.decompress((folder / LANDMARKS_FILE).read_bytes()).decode()
        except OSError, lzma.LZMAError, UnicodeDecodeError:
            text = ""
        rows = [row.split(_TAB) for row in text.splitlines()]
        rows = [row for row in rows if len(row) == _FIELDS]
        try:
            latitudes = np.array([float(row[1]) for row in rows], dtype=np.float64)
            longitudes = np.array([float(row[2]) for row in rows], dtype=np.float64)
        except ValueError:
            rows, latitudes, longitudes = [], np.array([]), np.array([])
        names = tuple(row[0] for row in rows)
        return cls(names, NearestIndex(latitudes, longitudes))

    def __len__(self) -> int:
        """How many landmarks the snapshot knows.

        Returns:
            Their number.
        """
        return len(self._names)

    def at(self, point: Point) -> str:
        """The landmark a photo was taken at.

        Args:
            point: The photo's position.

        Returns:
            The name of the nearest landmark within `NEAR_M`; empty for none.
        """
        found = self._index.nearest(point)
        if found is None or found[1] * _M_PER_KM > NEAR_M:
            return ""
        return self._names[found[0]]


@functools.cache
def shared_landmarks() -> Landmarks:
    """The landmarks of the snapshot, read at the first call only.

    Returns:
        Them.
    """
    return Landmarks.load()
