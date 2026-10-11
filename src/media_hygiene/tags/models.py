"""The vocabulary of tags: where a word comes from, and one word of one file.

A tag is valid for one version of a file (size, mtime), like every row of the index.
Each source is recomputed on its own; `vision` and `caption` rows are derived from the
cached descriptions, so that nothing is kept as truth that can be derived again;
`person` words are derived from the faces at each search, never stored.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from media_hygiene.index.descriptions import PhotoVersion


class TagSource(StrEnum):
    """Where a tag comes from: each one is recomputed independently."""

    VISION = "vision"  # the words a vision model gave
    CAPTION = "caption"  # its sentence, kept whole for the search
    FOLDER = "folder"  # the meaningful words of the folder names
    DATE = "date"  # year, month, season, holidays, calendar rules
    PLACE = "place"  # a personal place, the GeoNames town and country
    # The names of the people on the photo (`people`), made at each search from the
    # faces and `[[people.person]]`: never stored, never written into a sidecar.
    PERSON = "person"


class PlaceKind(StrEnum):
    """What a `place` word names: `xmp` writes each kind into its own field."""

    PERSONAL = "personal"  # a place of the user's (`[[classify.places]]`): Location
    TOWN = "town"  # the GeoNames town: City
    COUNTRY = "country"  # its country: Country


# Seconds of work per file: the sources computed without any model.
CHEAP_SOURCES: Final = (
    TagSource.FOLDER,
    TagSource.DATE,
    TagSource.PLACE,
)
MODEL_SOURCES: Final = (TagSource.VISION, TagSource.CAPTION)


@dataclass(frozen=True, slots=True)
class Tag:
    """One word (or one sentence) of one file, and who produced it."""

    source: TagSource
    value: str
    model: str = ""  # the vision model, for its sources; empty otherwise
    # For `place` words: what it names, several when a place shares its town's name
    # (`Luxembourg`, a town and a country); empty: another source, or not known yet.
    kinds: tuple[PlaceKind, ...] = ()


@dataclass(frozen=True, slots=True)
class FileTags:
    """The tags of one version of a file."""

    photo: PhotoVersion
    tags: tuple[Tag, ...]
