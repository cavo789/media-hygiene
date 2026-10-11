"""The cheap tags: the words of the folders, the date, the place. Seconds per run.

The vision model sees scenes and objects, never occasions nor places (measured, TODO
0072): `Pâques 2007`, `Durbuy` and `Noël` come from here. Each producer gives the
words of one source, kept once each (case ignored), in their first order.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.whereabouts import located_point
from media_hygiene.date_names import MONTHS
from media_hygiene.geo.distance import distance_km
from media_hygiene.tags.dates import date_words
from media_hygiene.tags.models import PlaceKind, Tag, TagSource

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.tags.context import TagContext

# A folder name is split on spaces, underscores, dots and punctuation, not on hyphens:
# `Saint-Nicolas` stays one word.
_SEPARATORS: Final = re.compile(r"[\s_.,;:()\[\]{}+&!?#]+")
_MONTH_WORDS: Final = frozenset(name for names in MONTHS for name in names)
# Words that link others in a folder name, never searched for on their own.
_LINKS: Final = frozenset(
    {"les", "des", "une", "aux", "chez", "avec", "pour", "sur", "dans", "par", "et"}
    | {"the", "and", "with", "for", "from", "at", "to", "of", "in", "on"}
    | {"het", "een", "met", "van", "voor"}
)


def cheap_tags(file: MediaInput, context: TagContext) -> tuple[Tag, ...]:
    """Every tag a file gets without a model.

    Args:
        file: The file, its root and what the index knows of it.
        context: Folder rules, calendar, places and towns.

    Returns:
        Its folder, date and place tags.
    """
    return (
        *_tags(TagSource.FOLDER, folder_words(file, context)),
        *_tags(TagSource.DATE, date_words(file, context)),
        *place_tags(file, context),
    )


def folder_words(file: MediaInput, context: TagContext) -> tuple[str, ...]:
    """The meaningful words of the folders between the root and the file.

    Args:
        file: The file and its root.
        context: The folder rules (generic and band folders) and stop words.

    Returns:
        `2019/Durbuy - ours` → `Durbuy`, `ours`; nothing for `DCIM/100CANON`.
    """
    labels = context.folders.meaning(file.path.parent, file.root)
    words = (word.strip("-") for label in labels for word in _SEPARATORS.split(label))
    return tuple(
        word
        for word in words
        if context.words.keeps(word)
        and word.casefold() not in _MONTH_WORDS
        and word.casefold() not in _LINKS
    )


def place_tags(file: MediaInput, context: TagContext) -> tuple[Tag, ...]:
    """Where the file was taken: a place of the user's, the town and its country.

    Args:
        file: The file and its metadata.
        context: The personal places and the towns.

    Returns:
        E.g. `Maison` (personal), `Durbuy` (town), `Belgique` (country), each once
        whatever its case; nothing without a GPS position.
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
        if name:
            seen.setdefault(name.casefold(), Tag(TagSource.PLACE, name, "", kind))
    return tuple(seen.values())


def _tags(source: TagSource, words: Iterable[str]) -> tuple[Tag, ...]:
    """Make tags of words, each once whatever its case.

    Args:
        source: Where they come from.
        words: The words, in order.

    Returns:
        The tags.
    """
    seen: dict[str, str] = {}
    for word in words:
        seen.setdefault(word.casefold(), word.strip())
    return tuple(Tag(source, word) for word in seen.values() if word)
