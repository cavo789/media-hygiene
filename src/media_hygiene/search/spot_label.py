"""What a tile says of where its photo was taken, read from the index (0545).

The landmark (the tile's chip) and the town (this line) are stored
(`index.spot_rows`); the user's own places and names of towns are read from the
settings at each show: a place drawn on the `places` page applies at once.
The regions (admin1, admin2) are searched, never shown here.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.classify.place_match import place_at, zones_of
from media_hygiene.geo.distance import Point
from media_hygiene.index.spot_rows import spots_by_key

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from media_hygiene.classify.place_match import Zone
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.index.spot_rows import StoredSpot
    from media_hygiene.search.fts import SearchIndex


@dataclass(frozen=True, slots=True)
class SpotNames:
    """The user's places and names of towns, to name a stored row."""

    zones: Sequence[Zone] = ()
    renames: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def of(cls, settings: ClassifySettings) -> SpotNames:
        """Read them from `[classify]`.

        Args:
            settings: `[classify]`.

        Returns:
            The names.
        """
        return cls(zones_of(settings.places), settings.town_names)

    def place(self, spot: StoredSpot) -> str:
        """The user's own place, else the town.

        Args:
            spot: The stored row.

        Returns:
            E.g. `Home`, `Liège`; empty when neither is known.
        """
        own = place_at(Point(spot.latitude, spot.longitude), self.zones)
        return own.name if own else self.renames.get(spot.town, spot.town)

    def label(self, spot: StoredSpot) -> str:
        """The place only: the landmark is the tile's 📍 chip (0651).

        Args:
            spot: The stored row.

        Returns:
            E.g. `Liège`; empty when no place or town is known.
        """
        return self.place(spot)


def spot_labels(
    connection: sqlite3.Connection, keys: Iterable[int], names: SpotNames
) -> dict[int, tuple[str, str]]:
    """The labels of some files; none for an index older than the rows.

    Args:
        connection: The index.
        keys: The files' keys.
        names: The user's places and names.

    Returns:
        Each located file's label and landmark (empty when none) by key: the
        landmark is the tile's 📍 chip (0651).
    """
    try:
        found = spots_by_key(connection, json.dumps(list(keys)))
    except sqlite3.OperationalError:
        return {}
    return {key: (names.label(spot), spot.landmark) for key, spot in found.items()}


def with_spots(index: SearchIndex, cards: list[dict[str, object]]) -> None:
    """Give the folder view's cards their labels.

    Args:
        index: The open index.
        cards: The cards, each with its `key`; completed in place.
    """
    keys = [int(str(card["key"])) for card in cards]
    labels = spot_labels(index.connection, keys, index.spot_names)
    for key, card in zip(keys, cards, strict=True):
        card["spot"], card["landmark"] = labels.get(key, ("", ""))
