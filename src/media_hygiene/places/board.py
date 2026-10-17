"""What the map page shows and changes: the clusters, the places, the town search.

The places live in `config.toml`; every save writes the file and reads it back, so
the page always shows what the next `classify` will read. The first photos of a
cluster are named by `review`'s preview key: a file changed since the audit gets a
new one. Pictures and videos are counted apart (0232): a cluster of one video is no
"1 photo". A cluster can be set aside (0234), its photos given a place by hand (0237).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.places.board_state import BoardView, board_state
from media_hygiene.places.config_aside import read_aside, restore, set_aside
from media_hygiene.places.config_file import read_places, save_places
from media_hygiene.places.config_photos import take_back
from media_hygiene.places.drawer_rows import Shown, drawer_rows
from media_hygiene.places.hand_desk import HandDesk, PhotosAction

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.config.classify_places import PersonalPlace
    from media_hygiene.config.places_settings import IgnoredSpot
    from media_hygiene.places.clusters import Cluster
    from media_hygiene.places.config_file import PlaceEdit
    from media_hygiene.places.folder_rows import FolderContext
    from media_hygiene.places.hand_desk import PhotosAct

SEARCH_LIMIT: Final = 8


class PlacesBoard:
    """The state of the map page, and the changes it asks for."""

    def __init__(self, clusters: Sequence[Cluster], context: FolderContext) -> None:
        """Read the places, the circles set aside and the photos given by hand.

        Args:
            clusters: Where the photos were taken.
            context: `config.toml`, the host paths, the GeoNames towns (the search).

        Raises:
            ValueError: The places of the file are invalid.
        """
        self._clusters = tuple(clusters)
        self._context = context
        self._places = read_places(context.config_file)
        self._aside = read_aside(context.config_file)
        self._hand = HandDesk(self._clusters, context)
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
        given = self._hand.given
        shown = (
            Shown(member.file, member.point)
            for member in self._clusters[rank].members
            if member.file.path not in given
        )
        return drawer_rows(shown, self._context.mapper, self._sources)

    def preview_source(self, key: str) -> Path | None:
        """Find the photo a preview key names.

        Args:
            key: The key, from the page.

        Returns:
            The file, in the container, or None for an unknown key.
        """
        return self._sources.get(key) or self._hand.sources.get(key)

    def state(self) -> dict[str, object]:
        """What the page shows (`board_state`).

        Returns:
            The places, the clusters, the circles set aside.
        """
        view = BoardView(self._clusters, self._places, self._aside, self._hand)
        return board_state(view)

    def save(self, edits: Sequence[PlaceEdit]) -> None:
        """Write the places into `config.toml`, then read them back.

        Args:
            edits: Every place, kept ones with their key.

        Raises:
            ValueError: Two places share a name, or two are home.
            OSError: The file cannot be written.
        """
        save_places(self._context.config_file, edits, renamed(self._places, edits))
        self._places = read_places(self._context.config_file)
        self._hand.reload()

    def set_aside(self, spot: IgnoredSpot) -> None:
        """Set the clusters of a circle aside, then read the circles back.

        Args:
            spot: The circle.

        Raises:
            ValueError: The file is not TOML.
            OSError: The file cannot be written.
        """
        set_aside(self._context.config_file, spot)
        self._aside = read_aside(self._context.config_file)

    def restore(self, spot: IgnoredSpot) -> None:
        """Take a circle set aside out of the file, then read the circles back.

        Args:
            spot: The circle, as read back.

        Raises:
            ValueError: The file is not TOML.
            OSError: The file cannot be written.
        """
        restore(self._context.config_file, spot)
        self._aside = read_aside(self._context.config_file)

    def place_photos(self, act: PhotosAct) -> None:
        """Give a cluster's photos to a place, or take one back; read back.

        Args:
            act: What the page asks.

        Raises:
            ValueError: An unknown cluster or place, or no photo to give.
            OSError: The file cannot be written.
        """
        if act.action is PhotosAction.REMOVE:
            take_back(self._context.config_file, act.sha256)
            self._hand.reload()
            return
        wanted = act.place.casefold()
        place = next((p.name for p in self._places if p.name.casefold() == wanted), "")
        if not place or not 0 <= act.cluster < len(self._clusters):
            raise ValueError(_("Unknown place or cluster: reload the page."))
        self._hand.give(self._clusters[act.cluster], act, place)

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


def renamed(
    old: Sequence[PersonalPlace], edits: Sequence[PlaceEdit]
) -> dict[str, str | None]:
    """The places a save renames (old name → new) or deletes (→ None).

    Args:
        old: The places as read back before the save.
        edits: Every place kept, with its key (its rank in `old`), and the new ones.

    Returns:
        The names that change.
    """
    kept = {edit.key: edit.place.name for edit in edits if edit.key is not None}
    return {
        place.name: kept.get(key)
        for key, place in enumerate(old)
        if kept.get(key) != place.name
    }
