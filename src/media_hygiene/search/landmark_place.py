"""A landmark just typed, offered as one of the user's places (0651).

Once the large view's *📍 Landmark…* wrote a name, the dialog asks whether to add it as
a place (`[[classify.places]]`): a circle of `DEFAULT_RADIUS_M` around the photo. It is
asked each time, never written silently; the answer is the file read back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.i18n import _
from media_hygiene.places.config_file import PlaceEdit, read_places, save_places

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.geo.point import Point


def add_place(config_file: Path, name: str, point: Point) -> str:
    """Add a circle named `name` around `point`, unless a place has that name.

    Args:
        config_file: `config.toml`.
        name: The landmark's name.
        point: The photo's position.

    Returns:
        The line to show, from the places read back.
    """
    places = read_places(config_file)
    if any(place.name.casefold() == name.casefold() for place in places):
        return _("{name} is already one of your places: kept.").format(name=name)
    new = PersonalPlace(name=name, latitude=point.latitude, longitude=point.longitude)
    edits = [PlaceEdit(rank, place) for rank, place in enumerate(places)]
    save_places(config_file, [*edits, PlaceEdit(None, new)])
    if not any(place.name == name for place in read_places(config_file)):
        return _("{name} could not be added to your places.").format(name=name)
    return _(
        "{name} is now one of your places ({radius} m around this photo),"
        " read back from config.toml."
    ).format(name=name, radius=round(new.radius_m))
