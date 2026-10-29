"""`[places]` — the map of `media-hygiene places`: its tiles, its online search.

Only the map tiles are fetched, by the browser: they reveal the areas viewed, never a
photo nor a position of one. The page's Content-Security-Policy allows that host only.
The online search of an area by its name asks `nominatim_url`, from the tool itself,
on a click only; empty, there is no online search. `[[places.folders]]` holds the
positions the user gave whole folders on the map: `xmp` writes them for the photos of
those folders that have none (0231). `[[places.ignored]]` holds the clusters the user
set aside, as circles: hidden from the map, `classify` unchanged (0234). `town_hint_km`:
a place named like a town within that distance gets a hint (0239). `reverse_lookup`:
after an `import`, whether the new photos' positions may be named online (0474): `ask`
each time (default No), `never`, or `always` (the user's standing Yes).
"""

from __future__ import annotations

from typing import Final, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from media_hygiene.i18n import _

OSM_TILES: Final = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
OSM_ATTRIBUTION: Final = "© OpenStreetMap contributors"  # plain text, shown as is
OSM_NOMINATIM: Final = "https://nominatim.openstreetmap.org"
_HTTPS: Final = "https"
_WEB: Final = frozenset({"http", _HTTPS})
_TILE_FIELDS: Final = ("{z}", "{x}", "{y}")
_SUBDOMAIN: Final = "{s}"
_ANY_SUBDOMAIN: Final = "*"
ASIDE_RADIUS_M: Final = 150  # a cluster's cell is about 200 m wide
MAX_ASIDE_RADIUS_M: Final = 50_000
TOWN_HINT_KM: Final = 10.0  # a place named like a town this close: the hint (0239)
MAX_TOWN_HINT_KM: Final = 200.0


class FolderPosition(BaseModel):
    """Where the photos of a folder were taken, set on the map of `places`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    folder: str = Field(min_length=1)  # a host path, as `protected` holds them
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class IgnoredSpot(BaseModel):
    """A cluster not worth a name: every cluster whose middle lies in this circle.

    A position, not the cluster's rank: the ranks and the grid may change between
    versions, and a later audit moves a middle by a few metres.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_m: float = Field(default=ASIDE_RADIUS_M, gt=0, le=MAX_ASIDE_RADIUS_M)


class PlacesSettings(BaseModel):
    """`[places]` — the tile server of the map, and the credit it asks for."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tiles: str = OSM_TILES
    attribution: str = OSM_ATTRIBUTION
    nominatim_url: str = OSM_NOMINATIM
    folders: tuple[FolderPosition, ...] = ()
    ignored: tuple[IgnoredSpot, ...] = ()
    town_hint_km: float = Field(default=TOWN_HINT_KM, gt=0, le=MAX_TOWN_HINT_KM)
    reverse_lookup: Literal["ask", "never", "always"] = "ask"

    @field_validator("nominatim_url")
    @classmethod
    def _search_url(cls, url: str) -> str:
        """Refuse a search address that is neither empty nor http(s).

        Args:
            url: The address of a Nominatim instance; empty: no online search.

        Returns:
            It, stripped.

        Raises:
            ValueError: It is not a web address.
        """
        url = url.strip()
        parts = urlsplit(url)
        if url and (parts.scheme not in _WEB or not parts.netloc):
            message = _("'{url}' is not an http:// or https:// address").format(url=url)
            raise ValueError(message)
        return url

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
            message = _("'{url}' is not an https:// address").format(url=tiles)
            raise ValueError(message)
        if not all(field in tiles for field in _TILE_FIELDS):
            message = _("'{url}' lacks {fields}").format(
                url=tiles, fields="{z}, {x} or {y}"
            )
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
