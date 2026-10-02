"""`[[classify.places]]` — the user's places: a name, a position, a radius or an area.

The radius exists only for these places: a town's name cannot tell home from the
bakery next door. A place can instead be an `area` drawn from OpenStreetMap (a village,
a park), kept in the file with its `osm` id: `classify` never goes online. One place
can be `home`: the reference of the `trip` rules. A name becomes a folder name:
unique, and one Windows accepts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, field_validator

from media_hygiene.classify.layout import check_layout
from media_hygiene.geo.areas import Shape, check_shape
from media_hygiene.geo.distance import Point

if TYPE_CHECKING:
    from collections.abc import Sequence

DEFAULT_RADIUS_M: Final = 200
MAX_RADIUS_M: Final = 50_000
MAX_LATITUDE: Final = 90
MAX_LONGITUDE: Final = 180
OSM_ID: Final = r"^([NWR][0-9]+)?$"  # a node, a way or a relation; empty: none


class PersonalPlace(BaseModel):
    """One place of the user's: the photos taken within `radius_m`, or in `area`.

    With an area, `latitude` and `longitude` are its middle, for the map and for trips
    measured from home; `radius_m` is not used.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    latitude: float = Field(ge=-MAX_LATITUDE, le=MAX_LATITUDE)
    longitude: float = Field(ge=-MAX_LONGITUDE, le=MAX_LONGITUDE)
    radius_m: float = Field(default=DEFAULT_RADIUS_M, gt=0, le=MAX_RADIUS_M)
    home: bool = False
    osm: str = Field(default="", pattern=OSM_ID)
    area: Shape | None = None

    @field_validator("area")
    @classmethod
    def _area(cls, area: Shape | None) -> Shape | None:
        """Refuse an area that cannot be one.

        Args:
            area: The polygons, or None for a circle.

        Returns:
            It, unchanged.
        """
        return area if area is None else check_shape(area)

    @field_validator("name")
    @classmethod
    def _folder_name(cls, name: str) -> str:
        """Refuse a name that cannot be a folder name.

        Args:
            name: The place's name.

        Returns:
            It, stripped.

        Raises:
            ValueError: It holds a placeholder or a character Windows refuses.
        """
        name = name.strip()
        if not name or "{" in name or "}" in name:
            message = f"{name!r} is not a place name: no braces, not empty"
            raise ValueError(message)
        check_layout(name)
        return name

    @property
    def point(self) -> Point:
        """The place's position.

        Returns:
            It.
        """
        return Point(self.latitude, self.longitude)


def check_places(places: Sequence[PersonalPlace]) -> None:
    """Refuse two places of the same name, or two homes.

    Args:
        places: The places.

    Raises:
        ValueError: A name is used twice, or more than one place is home.
    """
    seen: set[str] = set()
    for place in places:
        if place.name.casefold() in seen:
            message = f"two places are named {place.name!r}"
            raise ValueError(message)
        seen.add(place.name.casefold())
    homes = [place.name for place in places if place.home]
    if len(homes) > 1:
        message = f"only one place can be home, not {', '.join(homes)}"
        raise ValueError(message)
