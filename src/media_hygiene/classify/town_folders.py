"""Which folders are named after a town: the guess `classify` and `xmp` share.

A folder matches only when its whole name is a town's (case, accents and hyphens aside),
never a word inside it, and only towns of `folder_town_min_population` inhabitants
count. Among homonyms, the countries of the collection's GPS photos and of home win,
then the most populous. Months and seasons are never towns (`Mai`, `Été`). The located
photos of the folder have the last word: farther than `trip_merge_max_km` from the
town, the folder is not named after it.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.former import FormerHint
from media_hygiene.date_names import MONTHS
from media_hygiene.geo.distance import Point, centre, distance_km
from media_hygiene.geo.folding import town_key
from media_hygiene.tags.vocabulary import SEASON_NAMES

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.geo.gazetteer import Gazetteer, Town

_GRID: Final = 10  # GPS positions rounded to 0.1 degree to find their countries
_THOUSAND: Final = 1000
# Words of dates are folder names first: `2017/Mai` is May, not Mai in Kenya.
_NOT_TOWNS: Final = frozenset(
    town_key(word) for words in (*MONTHS, *SEASON_NAMES.values()) for word in words
)


@dataclass(frozen=True, slots=True)
class TownFolders:
    """Each folder named after a town and the files below it; how each was found."""

    folders: Mapping[tuple[Path, Town], Sequence[Path]]
    hints: Mapping[Path, FormerHint]  # the folders of removed copies that named it


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
        found = self.by_name.get(town_key(folder), ())
        return max(
            found,
            key=lambda town: (town.country in self.countries, town.population_k),
            default=None,
        )


def town_folders(
    files: Sequence[MediaInput],
    points: Mapping[Path, Point],
    config: tuple[ClassifySettings, Gazetteer],
) -> TownFolders:
    """The folders named after a town, those whose photos lie elsewhere left out.

    Args:
        files: The files.
        points: The position of each located file.
        config: `[classify]`, and the GeoNames towns.

    Returns:
        Each folder, its town and its files.
    """
    settings, towns = config
    folders, hints = _by_folder(files, _towns(towns, settings, points))
    kept: dict[tuple[Path, Town], tuple[Path, ...]] = {}
    for (folder, town), paths in folders.items():
        located = [points[path] for path in paths if path in points]
        if located and distance_km(centre(located), town.point) > (
            settings.trip_merge_max_km
        ):
            continue  # its photos say it was taken elsewhere
        kept[folder, town] = tuple(paths)
    return TownFolders(kept, hints)


def _by_folder(
    files: Sequence[MediaInput], known: _Towns
) -> tuple[dict[tuple[Path, Town], list[Path]], dict[Path, FormerHint]]:
    """Group the files by the nearest folder above them named after a town.

    Args:
        files: The files.
        known: The towns, by name.

    Returns:
        Each such folder, its town, and the files below it (or whose removed copies
        lay below it); the folders of removed copies each of those files read.
    """
    names: dict[str, Town | None] = {}  # folder names are few: each is looked up once

    def named(name: str) -> Town | None:
        """The town a folder name names, looked up once.

        Args:
            name: A folder name.

        Returns:
            The town, or None.
        """
        if name not in names:
            names[name] = known.named(name) if name else None
        return names[name]

    folders: dict[tuple[Path, Town], list[Path]] = defaultdict(list)
    hints: dict[Path, FormerHint] = {}
    for file in files:
        found = _town_folder(file.path, file.root, named)
        if found is None and file.former:
            former = {
                town
                for copy in file.former
                if (town := _town_folder(copy.path, copy.root, named)) is not None
            }
            if len({town for _folder, town in former}) == 1:
                found = min(former, key=lambda pair: pair[0])
                hints[file.path] = FormerHint(tuple(sorted(f for f, _t in former)))
        if found is not None:
            folders[found].append(file.path)
    return folders, hints


def _town_folder(
    path: Path, root: Path, named: Callable[[str], Town | None]
) -> tuple[Path, Town] | None:
    """The nearest folder above a file named after a town.

    Args:
        path: The file.
        root: The mounted folder it lies in: the folders above are not read.
        named: The town of a folder name, or None.

    Returns:
        The folder and its town, or None.
    """
    for folder in path.relative_to(root).parents:
        town = named(folder.name)
        if town is not None:
            return root / folder, town
    return None


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
    ignored = _NOT_TOWNS | {town_key(name) for name in settings.folder_town_ignore}
    by_name: dict[str, list[Town]] = defaultdict(list)
    for index, names in enumerate(zip(towns.geonames, towns.names, strict=True)):
        town = towns.town(index)
        if town.population_k * _THOUSAND < least:
            continue
        for key in {town_key(name) for name in names} - ignored:
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
