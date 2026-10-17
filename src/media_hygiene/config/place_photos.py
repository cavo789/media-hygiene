"""`[[classify.place_photos]]` — photos given a place by hand, their GPS wrong (0237).

A phone indoors often records a position off by a street or two: the photos taken at
the grandparents' are placed elsewhere in the village. Neither a larger circle nor a
second zone fixes it (they would name the whole village, or a real photo taken at that
spot): these photos only are given to the place. A photo is known by its content, its
size then its SHA-256, never by its path: `sort`, `undo`, the quarantine or a folder
renamed in Explorer change nothing. `path` is the host path when it was given, for the
reader only. A photo edited since (new content) falls back to its GPS.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.config.classify_places import PersonalPlace

SHA256: Final = r"^[0-9a-f]{64}$"


class HandPhoto(BaseModel):
    """One photo given a place: its content, and where it was when given."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    sha256: str = Field(pattern=SHA256)
    size: int = Field(ge=0)
    path: str = ""  # host path when given: for the reader only


class PlacePhotos(BaseModel):
    """The photos given one of the `[[classify.places]]`, whatever their GPS says."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    place: str = Field(min_length=1)
    photos: tuple[HandPhoto, ...] = ()


def check_place_photos(
    places: Sequence[PersonalPlace], given: Sequence[PlacePhotos]
) -> None:
    """Refuse photos given to a place that does not exist.

    Args:
        places: The user's places.
        given: The photos given by hand.

    Raises:
        ValueError: An entry names no place of `[[classify.places]]`.
    """
    names = {place.name.casefold() for place in places}
    for entry in given:
        if entry.place.casefold() not in names:
            message = _(
                "[[classify.place_photos]] names '{name}', which is no "
                "[[classify.places]]"
            ).format(name=entry.place)
            raise ValueError(message)
