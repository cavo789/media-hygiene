"""The tiles under the storyteller's small map (0449), when `[places] tiles` is set.

By default the phone draws the event's towns as labels: nothing leaves the network.
When the user wrote `[places] tiles` (the map of `places`), the phone's browser fetches
those tiles: the tile server then sees the area viewed, never a photo. The remote's
Content-Security-Policy allows that host only, as `places` does.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.places.app import PAGE_REFERRER
from media_hygiene.review.http import NO_REFERRER
from media_hygiene.review.videos import NEAR_POLICY

if TYPE_CHECKING:
    from media_hygiene.config.places_settings import PlacesSettings

_IMAGES: Final = "img-src 'self'"
_TILES_FIELD: Final = "tiles"


@dataclass(frozen=True, slots=True)
class MapTiles:
    """The tiles the remote may show, its policy and referrer."""

    url: str = ""  # empty: towns as labels, offline
    credit: str = ""
    policy: str = NEAR_POLICY
    referrer: str = NO_REFERRER


def map_tiles(places: PlacesSettings) -> MapTiles:
    """The tiles of the remote's map: only when the user set `[places] tiles`.

    Args:
        places: `[places]`.

    Returns:
        The tiles, or none (the default `places` tiles are not used here).
    """
    if _TILES_FIELD not in places.model_fields_set:
        return MapTiles()
    policy = NEAR_POLICY.replace(_IMAGES, f"{_IMAGES} {places.tile_host}")
    return MapTiles(places.tiles, places.attribution, policy, PAGE_REFERRER)
