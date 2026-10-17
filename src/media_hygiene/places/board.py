"""What the map page shows and changes: the clusters, the places, the town search.

The places live in `config.toml`; every save writes the file and reads it back, so
the page always shows what the next `classify` will read. The first photos of a
cluster are named by `review`'s preview key: a file changed since the audit gets a
new one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.places.clusters import named
from media_hygiene.places.config_file import read_places, save_places
from media_hygiene.review.views import PREVIEW_PREFIX, preview_key

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.geo.gazetteer import Gazetteer
    from media_hygiene.places.clusters import Cluster
    from media_hygiene.places.config_file import PlaceEdit

SEARCH_LIMIT: Final = 8
JPEG: Final = ".jpg"


class PlacesBoard:
    """The state of the map page, and the changes it asks for."""

    def __init__(
        self, clusters: Sequence[Cluster], config_file: Path, towns: Gazetteer
    ) -> None:
        """Read the places already written.

        Args:
            clusters: Where the photos were taken.
            config_file: `config.toml`.
            towns: The GeoNames towns, for the search.

        Raises:
            ValueError: The places of the file are invalid.
        """
        self._clusters = tuple(clusters)
        self._config_file = config_file
        self._towns = towns
        self._places = read_places(config_file)
        self._sources = {
            preview_key(member.file): member.file.path
            for cluster in self._clusters
            for member in cluster.members
        }

    def photos(self, rank: int) -> list[dict[str, object]] | None:
        """The first photos of a cluster, for its grid of previews.

        Args:
            rank: Its rank in the state's clusters, the largest first.

        Returns:
            Each photo's name, preview, position, and whether it is still there (a
            file moved since the audit, or a folder not mounted, is not); None for
            an unknown rank.
        """
        if not 0 <= rank < len(self._clusters):
            return None
        return [
            {
                "name": member.file.path.name,
                "preview": f"{PREVIEW_PREFIX}{preview_key(member.file)}{JPEG}",
                "latitude": member.point.latitude,
                "longitude": member.point.longitude,
                "found": member.file.path.is_file(),
            }
            for member in self._clusters[rank].members
        ]

    def preview_source(self, key: str) -> Path | None:
        """Find the photo a preview key names.

        Args:
            key: The key, from the page.

        Returns:
            The file, in the container, or None for an unknown key.
        """
        return self._sources.get(key)

    def state(self) -> dict[str, object]:
        """What the page shows.

        Returns:
            The places, with their rank in the file, and the clusters with the name
            of the place each lies in.
        """
        return {
            "places": [
                {"key": key, **place.model_dump()}
                for key, place in enumerate(self._places)
            ],
            "clusters": [
                (point.latitude, point.longitude, item.cluster.count, item.place)
                for item in named(self._clusters, self._places)
                for point in (item.cluster.point,)
            ],
        }

    def save(self, edits: Sequence[PlaceEdit]) -> None:
        """Write the places into `config.toml`, then read them back.

        Args:
            edits: Every place, kept ones with their key.

        Raises:
            ValueError: Two places share a name, or two are home.
            OSError: The file cannot be written.
        """
        save_places(self._config_file, edits)
        self._places = read_places(self._config_file)

    def search(self, text: str) -> list[dict[str, object]]:
        """Find towns by the start of their name, offline.

        Args:
            text: What the user typed.

        Returns:
            The towns, the largest first.
        """
        return [
            {
                "name": town.name,
                "region": town.region,
                "country": town.country,
                "latitude": town.point.latitude,
                "longitude": town.point.longitude,
            }
            for town in self._towns.search(text, SEARCH_LIMIT)
        ]
