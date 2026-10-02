"""`[places]` — the map of `media-hygiene places`: where its tiles come from.

Only the map tiles are fetched, by the browser: they reveal the areas viewed, never a
photo nor a position of one. The page's Content-Security-Policy allows that host only.
"""

from __future__ import annotations

from typing import Final
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, field_validator

OSM_TILES: Final = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
OSM_ATTRIBUTION: Final = "© OpenStreetMap contributors"  # plain text, shown as is
_HTTPS: Final = "https"
_TILE_FIELDS: Final = ("{z}", "{x}", "{y}")
_SUBDOMAIN: Final = "{s}"
_ANY_SUBDOMAIN: Final = "*"


class PlacesSettings(BaseModel):
    """`[places]` — the tile server of the map, and the credit it asks for."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tiles: str = OSM_TILES
    attribution: str = OSM_ATTRIBUTION

    @field_validator("tiles")
    @classmethod
    def _tile_url(cls, tiles: str) -> str:
        """Refuse a tile address that is not HTTPS or lacks `{z}`, `{x}`, `{y}`.

        Args:
            tiles: The address of the tiles.

        Returns:
            It, unchanged.

        Raises:
            ValueError: It cannot serve tiles safely.
        """
        parts = urlsplit(tiles)
        if parts.scheme != _HTTPS or not parts.netloc:
            message = f"{tiles!r} is not an https:// address"
            raise ValueError(message)
        if not all(field in tiles for field in _TILE_FIELDS):
            message = f"{tiles!r} lacks {{z}}, {{x}} or {{y}}"
            raise ValueError(message)
        return tiles

    @property
    def tile_host(self) -> str:
        """The origin of the tiles, for the Content-Security-Policy.

        Returns:
            E.g. `https://tile.openstreetmap.org`; `{s}` subdomains become `*`.
        """
        host = urlsplit(self.tiles).netloc.replace(_SUBDOMAIN, _ANY_SUBDOMAIN)
        return f"{_HTTPS}://{host}"
