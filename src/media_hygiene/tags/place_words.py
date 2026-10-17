"""The place words of a file: a place of the user's, the town and its country."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.classify.whereabouts import located_point
from media_hygiene.geo.distance import distance_km
from media_hygiene.tags.models import PlaceKind, Tag, TagSource

if TYPE_CHECKING:
    from media_hygiene.classify.models import MediaInput
    from media_hygiene.tags.context import TagContext


def place_tags(file: MediaInput, context: TagContext) -> tuple[Tag, ...]:
    """Where the file was taken: a place of the user's, the town and its country.

    Args:
        file: The file and its metadata.
        context: The personal places and the towns.

    Returns:
        E.g. `Maison` (personal), `Durbuy` (town), `Belgique` (country), each once
        whatever its case, with every kind it names (`Luxembourg`: town and
        country); nothing without a GPS position.
    """
    point = located_point(file.metadata)
    if point is None:
        return ()
    found = [
        (zone.place.name, PlaceKind.PERSONAL)
        for zone in context.places
        if zone.rank(point) is not None
    ]
    town = context.towns.nearest(point) if context.towns is not None else None
    if town is not None and distance_km(point, town.point) <= context.town_km:
        found.extend(((town.name, PlaceKind.TOWN), (town.country, PlaceKind.COUNTRY)))
    seen: dict[str, Tag] = {}
    for word, kind in found:
        name = word.strip()
        if not name:
            continue
        known = seen.get(name.casefold(), Tag(TagSource.PLACE, name))
        if kind not in known.kinds:
            known = replace(known, kinds=(*known.kinds, kind))
        seen[name.casefold()] = known
    return tuple(seen.values())
