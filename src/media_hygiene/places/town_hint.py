"""A place named like a town nearby: a hint, never a refusal (0239).

`classify` already names the photos of a town from GeoNames; a place of that name is
redundant unless it gives exact borders (an OpenStreetMap area) or another name, or the
town is too small for the towns list. So the page says it, and the save still works.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.geo.distance import distance_km
from media_hygiene.geo.folding import town_key
from media_hygiene.geo.point import Point

if TYPE_CHECKING:
    from media_hygiene.geo.gazetteer import Gazetteer

NEAR_KM: Final = 10.0
# Towns that start with the name, the largest first: enough to hold every namesake.
CANDIDATES: Final = 500


class HintAsk(BaseModel):
    """`POST /api/hint`: the name typed and where the place lies."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


def town_nearby(towns: Gazetteer, name: str, where: Point) -> str:
    """The GeoNames town a place of that name duplicates, if any.

    Args:
        towns: The towns.
        name: The place's name.
        where: The place's middle.

    Returns:
        The town's name, or "" when none of that name lies within `NEAR_KM`.
    """
    wanted = town_key(name)
    if not wanted:
        return ""
    for town in towns.search(name, CANDIDATES):
        if town_key(town.name) == wanted and distance_km(where, town.point) <= NEAR_KM:
            return town.name
    return ""


class TownHints:
    """`town_nearby` for the saved places, remembered: the towns scan is not free."""

    def __init__(self, towns: Gazetteer) -> None:
        """Start with nothing remembered.

        Args:
            towns: The towns.
        """
        self._towns = towns
        self._known: dict[tuple[str, float, float], str] = {}

    def of(self, name: str, where: Point) -> str:
        """The town a place duplicates, or "".

        Args:
            name: The place's name.
            where: Its middle.

        Returns:
            The town's name, or "".
        """
        key = (name, where.latitude, where.longitude)
        if key not in self._known:
            self._known[key] = town_nearby(self._towns, name, where)
        return self._known[key]

    def mark(self, state: dict[str, object]) -> dict[str, object]:
        """Add `town` to each place of the state (the hint, or "").

        Args:
            state: The board's state.

        Returns:
            The same state.
        """
        places = state["places"]
        assert isinstance(places, list)  # noqa: S101  # board_state builds a list
        for place in places:
            where = Point(place["latitude"], place["longitude"])
            place["town"] = self.of(place["name"], where)
        return state
