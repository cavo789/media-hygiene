"""Folders named after a town (`2017/Durbuy`): a place told by the folder, to check.

Few photos carry a GPS position; their folders often name where they were taken: the
`folder_town` rule. Which folder names which town is told by `town_folders`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.layout import GeoValues
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.town_folders import town_folders
from media_hygiene.classify.whereabouts import Spot

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.geo.distance import Point
    from media_hygiene.geo.gazetteer import Gazetteer


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
    found = town_folders(files, points, (settings, towns))
    spots: dict[Path, Spot] = {}
    for (_folder, town), paths in found.folders.items():
        values = GeoValues(country=town.country, region=town.region, city=town.name)
        spots.update({path: Spot(values, hint=found.hints.get(path)) for path in paths})
    return spots
