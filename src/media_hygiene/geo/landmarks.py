"""The landmarks of GeoNames, read offline: the monument a photo was taken at (0472).

The snapshot's `landmarks.tsv.xz` (see `ATTRIBUTION.txt`) lists monuments, castles,
churches, museums, towers… as GeoNames names and places them (classes S and L, the
codes of `tests/support/geonames/landmarks.py`). A photo is said to be at one when it
was taken within `NEAR_M` of it. No position ever leaves the machine. A snapshot
without the file (older) knows no landmark: the towns still answer. Only the landmarks
of the one-degree cells holding a photo are kept (0479, `near_cells`): continents never
photographed are not loaded.
"""

from __future__ import annotations

import functools
import lzma
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.geo.gazetteer import GEO_DATA
from media_hygiene.geo.nearest import NearestIndex, cell_of

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.geo.distance import Point

Cells = frozenset[tuple[int, int]]

LANDMARKS_FILE: Final = "landmarks.tsv.xz"
# How close a photo is taken to a landmark to be named after it: GeoNames places a
# landmark by one point (its centre, give or take), a phone's GPS errs by 5-50 m.
NEAR_M: Final = 200.0
_FIELDS: Final = 3  # name, latitude, longitude
_TAB: Final = "\t"
_M_PER_KM: Final = 1000.0
_RING: Final = (-1, 0, 1)


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
    def load(cls, folder: Path = GEO_DATA, cells: Cells | None = None) -> Landmarks:
        """Read the landmarks of a snapshot; none when its file is missing or damaged.

        Args:
            folder: Where its files lie.
            cells: The one-degree cells to keep (see `near_cells`); None keeps all.

        Returns:
            The landmarks.
        """
        try:
            text = lzma.decompress((folder / LANDMARKS_FILE).read_bytes()).decode()
        except OSError, lzma.LZMAError, UnicodeDecodeError:
            text = ""
        names: list[str] = []
        latitudes: list[float] = []
        longitudes: list[float] = []
        for line in text.splitlines():
            row = line.split(_TAB)
            if len(row) != _FIELDS:
                continue
            try:
                latitude, longitude = float(row[1]), float(row[2])
            except ValueError:
                continue
            if cells is None or cell_of(latitude, longitude) in cells:
                names.append(row[0])
                latitudes.append(latitude)
                longitudes.append(longitude)
        index = NearestIndex(
            np.array(latitudes, dtype=np.float64),
            np.array(longitudes, dtype=np.float64),
        )
        return cls(tuple(names), index)

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


def near_cells(points: Iterable[Point]) -> Cells:
    """The cells a landmark of these photos may lie in: theirs and the eight around.

    Args:
        points: The positions of the photos.

    Returns:
        The cells (a landmark 200 m away may lie across a cell's edge).
    """
    return frozenset(
        cell_of(point.latitude + row, point.longitude + column)
        for point in points
        for row in _RING
        for column in _RING
    )


@functools.lru_cache(maxsize=1)
def shared_landmarks(cells: Cells) -> Landmarks:
    """The landmarks of these cells, read again only when the cells change.

    Args:
        cells: The cells holding a photo (`near_cells`).

    Returns:
        Them.
    """
    return Landmarks.load(cells=cells)
