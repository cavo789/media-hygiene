"""The towns of GeoNames, read offline: the nearest one, and a search by name.

The snapshot lies in `data/` (see `ATTRIBUTION.txt`): towns of more than 1,000
inhabitants, their region, and the country names in each language of the interface.
No position ever leaves the machine.
"""

from __future__ import annotations

import lzma
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.constants import Locale
from media_hygiene.errors import GeoDataError
from media_hygiene.geo.distance import Point
from media_hygiene.geo.nearest import NearestIndex
from media_hygiene.geo.towns_file import TownRows, read_table, read_towns
from media_hygiene.i18n import _, active_locale

if TYPE_CHECKING:
    from collections.abc import Mapping


GEO_DATA: Final = Path(__file__).parent / "data"
TOWNS_FILE: Final = "towns.tsv.xz"
COUNTRIES_FILE: Final = "countries.tsv"
REGIONS_FILE: Final = "regions.tsv"


@dataclass(frozen=True, slots=True)
class Town:
    """A town, its region and its country, named in the language in use."""

    name: str
    point: Point
    country: str
    region: str
    population_k: int  # thousands of inhabitants


class Gazetteer:
    """The towns of the snapshot, ready to answer."""

    def __init__(
        self,
        rows: TownRows,
        index: NearestIndex,
        names: tuple[Mapping[str, Mapping[Locale, str]], Mapping[str, str]],
    ) -> None:
        """Keep the towns, their index, and the names of countries and regions.

        Args:
            rows: The towns.
            index: Their positions.
            names: Country names by code and language; region names by code.
        """
        self._rows = rows
        self._index = index
        self._countries, self._regions = names
        self._folded: tuple[str, ...] = ()  # the names, folded on the first search

    @classmethod
    def load(cls, folder: Path = GEO_DATA) -> Gazetteer:
        """Read a snapshot.

        Args:
            folder: Where its files lie.

        Returns:
            The gazetteer.

        Raises:
            GeoDataError: A file is missing or damaged.
        """
        try:
            rows = read_towns(folder / TOWNS_FILE)
            countries = {
                row[0]: {Locale.EN: row[1], Locale.FR: row[2]}
                for row in read_table(folder / COUNTRIES_FILE)
            }
            regions = {row[0]: row[1] for row in read_table(folder / REGIONS_FILE)}
        except (OSError, ValueError, IndexError, lzma.LZMAError) as exc:
            message = _("The towns used to name places cannot be read: {error}.")
            raise GeoDataError(message.format(error=exc)) from exc
        index = NearestIndex(rows.latitudes, rows.longitudes)
        return cls(rows, index, (countries, regions))

    def nearest(self, point: Point) -> Town | None:
        """The town nearest to a position.

        Args:
            point: A position.

        Returns:
            The town, or None for an empty snapshot.
        """
        found = self._index.nearest(point)
        return None if found is None else self.town(found[0])

    def main_town(self, point: Point, radius_km: float) -> Town | None:
        """The largest town around a position, else the nearest one.

        A district or a suburb is a town of its own in GeoNames: a trip to Sydney is
        named after Sydney, not after the suburb of its hotel.

        Args:
            point: A position.
            radius_km: How far around it a larger town wins.

        Returns:
            The town, or None for an empty snapshot.
        """
        around = self._index.within(point, radius_km)
        if not around.size:
            return self.nearest(point)
        population = self._rows.population_k[around]
        return self.town(int(around[int(np.argmax(population))]))

    def search(self, text: str, limit: int) -> tuple[Town, ...]:
        """The towns whose name starts with a text, the largest first.

        Case and accents do not matter: `liege` finds Liège.

        Args:
            text: The start of a name.
            limit: How many towns at most.

        Returns:
            The towns found.
        """
        wanted = fold(text)
        if not wanted:
            return ()
        if not self._folded:
            self._folded = tuple(fold(name) for name in self._rows.names)
        found = [i for i, name in enumerate(self._folded) if name.startswith(wanted)]
        population = self._rows.population_k
        found.sort(key=lambda index: -int(population[index]))
        return tuple(self.town(index) for index in found[:limit])

    def town(self, index: int) -> Town:
        """One town of the snapshot.

        Args:
            index: Its row.

        Returns:
            The town, its country named in the language in use.
        """
        rows = self._rows
        code = rows.countries[index]
        country = self._countries.get(code, {}).get(active_locale()) or code
        return Town(
            rows.names[index],
            Point(float(rows.latitudes[index]), float(rows.longitudes[index])),
            country,
            self._regions.get(rows.regions[index], ""),
            int(rows.population_k[index]),
        )

    @property
    def names(self) -> tuple[str, ...]:
        """The name of every town, by row.

        Returns:
            Them.
        """
        return self._rows.names


def fold(text: str) -> str:
    """A text without case nor accents, to compare names.

    Args:
        text: A name.

    Returns:
        It, folded: `Liège` → `liege`.
    """
    decomposed = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))
