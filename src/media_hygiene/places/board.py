"""What the map page shows and changes: the clusters, the places, the town search.

The places live in `config.toml`; every save writes the file and reads it back, so
the page always shows what the next `classify` will read. The first photos of a
cluster are named by `review`'s preview key: a file changed since the audit gets a
new one. Pictures and videos are counted apart (0232): a cluster of one video is no
"1 photo".
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.places.clusters import named
from media_hygiene.places.config_file import read_places, save_places
from media_hygiene.places.drawer_rows import Shown, drawer_rows

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.places.clusters import Cluster
    from media_hygiene.places.config_file import PlaceEdit
    from media_hygiene.places.folder_rows import FolderContext

SEARCH_LIMIT: Final = 8


class PlacesBoard:
    """The state of the map page, and the changes it asks for."""

    def __init__(self, clusters: Sequence[Cluster], context: FolderContext) -> None:
        """Read the places already written.

        Args:
            clusters: Where the photos were taken.
            context: `config.toml`, the host paths, the GeoNames towns (the search).

        Raises:
            ValueError: The places of the file are invalid.
        """
        self._clusters = tuple(clusters)
        self._context = context
        self._places = read_places(context.config_file)
        self._sources: dict[str, Path] = {}

    def photos(self, rank: int) -> list[dict[str, object]] | None:
        """The first photos and videos of a cluster, grouped by folder (`drawer_rows`).

        Args:
            rank: Its rank in the state's clusters, the largest first.

        Returns:
            Each file's name, host folder, previews, position, and whether it is
            still there (a file moved since the audit, or a folder not mounted, is
            not); None for an unknown rank.
        """
        if not 0 <= rank < len(self._clusters):
            return None
        members = self._clusters[rank].members
        shown = (Shown(member.file, member.point) for member in members)
        return drawer_rows(shown, self._context.mapper, self._sources)

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
            The places, with their rank in the file, and the clusters: their middle,
            their pictures and videos, the name of the place each lies in.
        """
        return {
            "places": [
                {"key": key, **place.model_dump()}
                for key, place in enumerate(self._places)
            ],
            "clusters": [
                (
                    point.latitude,
                    point.longitude,
                    found.pictures,
                    found.videos,
                    item.place,
                )
                for item in named(self._clusters, self._places)
                for found in (item.cluster,)
                for point in (found.point,)
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
        save_places(self._context.config_file, edits)
        self._places = read_places(self._context.config_file)

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
            for town in self._context.towns.search(text, SEARCH_LIMIT)
        ]
