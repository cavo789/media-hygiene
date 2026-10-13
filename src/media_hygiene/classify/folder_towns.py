"""Folders named after a town (`2017/Durbuy`): a place told by the folder, to check.

Few photos carry a GPS position; their folders often name where they were taken. A
folder matches only when its whole name is a town's (case and accents aside), never a
word inside it, and only towns of `folder_town_min_population` inhabitants count. Among
homonyms, the countries of the collection's GPS photos and of home win, then the most
populous. Month and season names are never towns (`Mai`, `Été`). The located photos of
the folder have the last word: farther than `trip_merge_max_km` from the town, the
folder is not named after it.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.layout import GeoValues
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.whereabouts import Spot
from media_hygiene.date_names import MONTHS
from media_hygiene.geo.distance import Point, centre, distance_km
from media_hygiene.geo.folding import fold
from media_hygiene.tags.vocabulary import SEASON_NAMES

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.geo.gazetteer import Gazetteer, Town

_GRID: Final = 10  # GPS positions rounded to 0.1 degree to find their countries
_THOUSAND: Final = 1000
# Words of dates are folder names first: `2017/Mai` is May, not Mai in Kenya.
_NOT_TOWNS: Final = frozenset(
    fold(word) for words in (*MONTHS, *SEASON_NAMES.values()) for word in words
)


@dataclass(frozen=True, slots=True)
class _Towns:
    """The towns large enough, by folded name, and the countries to prefer."""

    by_name: Mapping[str, tuple[Town, ...]]
    countries: frozenset[str]

    def named(self, folder: str) -> Town | None:
        """The town a folder is named after.

        Args:
            folder: The folder's name.

        Returns:
            The town, the preferred country first, then the most populous; None.
        """
        found = self.by_name.get(fold(folder), ())
        return max(
            found,
            key=lambda town: (town.country in self.countries, town.population_k),
            default=None,
        )


def folder_town_spots(
    files: Sequence[MediaInput],
    points: Mapping[Path, Point],
    config: tuple[ClassifySettings, Gazetteer | None],
) -> dict[Path, Spot]:
    """The files in a folder named after a town.

    Args:
        files: The files.
        points: The position of each located file.
        config: `[classify]`, and the GeoNames towns (None: no town rule is on).

    Returns:
        The town of each file whose folder (the nearest one named so) is a town's.
    """
    settings, towns = config
    on = any(r.match is RuleMatch.FOLDER_TOWN and r.score != 0 for r in settings.rules)
    if towns is None or not on:
        return {}
    spots: dict[Path, Spot] = {}
    for (_folder, town), paths in _by_folder(files, _towns(towns, settings, points)):
        located = [points[path] for path in paths if path in points]
        if located and distance_km(centre(located), town.point) > (
            settings.trip_merge_max_km
        ):
            continue  # its photos say it was taken elsewhere
        values = GeoValues(country=town.country, region=town.region, city=town.name)
        spots.update(dict.fromkeys(paths, Spot(values)))
    return spots


def _by_folder(
    files: Sequence[MediaInput], known: _Towns
) -> Iterable[tuple[tuple[Path, Town], list[Path]]]:
    """Group the files by the nearest folder above them named after a town.

    Args:
        files: The files.
        known: The towns, by name.

    Returns:
        Each such folder, its town, and the files below it.
    """
    named: dict[str, Town | None] = {}  # folder names are few: each is looked up once
    folders: dict[tuple[Path, Town], list[Path]] = defaultdict(list)
    for file in files:
        for folder in file.path.relative_to(file.root).parents:
            if folder.name not in named:
                named[folder.name] = known.named(folder.name) if folder.name else None
            town = named[folder.name]
            if town is not None:
                folders[file.root / folder, town].append(file.path)
                break
    return folders.items()


def _towns(
    towns: Gazetteer, settings: ClassifySettings, points: Mapping[Path, Point]
) -> _Towns:
    """Index the towns large enough by their names, GeoNames' and the user's.

    Args:
        towns: The GeoNames towns, the user's names applied.
        settings: The population threshold and home.
        points: The located files: their countries are preferred.

    Returns:
        The index.
    """
    least = settings.folder_town_min_population
    by_name: dict[str, list[Town]] = defaultdict(list)
    for index, names in enumerate(zip(towns.geonames, towns.names, strict=True)):
        town = towns.town(index)
        if town.population_k * _THOUSAND < least:
            continue
        for key in {fold(name) for name in names} - _NOT_TOWNS:
            by_name[key].append(town)
    grid = {
        Point(round(p.latitude * _GRID) / _GRID, round(p.longitude * _GRID) / _GRID)
        for p in points.values()
    }
    homes = [place.point for place in settings.places if place.home]
    countries = frozenset(
        near.country for p in (*grid, *homes) if (near := towns.nearest(p)) is not None
    )
    return _Towns({key: tuple(found) for key, found in by_name.items()}, countries)
