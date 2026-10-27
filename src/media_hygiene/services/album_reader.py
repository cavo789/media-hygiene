"""The albums a phone or the PC shows (0297): `albums.json`, read through the index.

Each answer opens the index read-only for its own time: the home page's audit may write
it meanwhile, and a fresh install has none yet (said, never a traceback). The towns
(GeoNames, offline) are loaded once, at the first photo with a GPS position. The
pictures sized for a phone are `slideshow`'s (0291), fitted into a square: a photo
taken upright fills the phone held upright, one taken sideways the phone turned.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import GeoDataError, MountError
from media_hygiene.geo.distance import distance_km
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.i18n import _
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.pictures import Pictures
from media_hygiene.services.albums import album_store
from media_hygiene.services.data_checks import unreadable_index
from media_hygiene.services.slideshow_pick import Pick, picked_slides
from media_hygiene.share.album_cover import cover_key
from media_hygiene.share.album_view import AlbumSeen, album_view
from media_hygiene.slideshow.pictures import ShowPictures
from media_hygiene.slideshow.screen_jpeg import SQUARE, ScreenJob

if TYPE_CHECKING:
    from collections.abc import Iterator
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.geo.distance import Point
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.album_shelf import Keyed
    from media_hygiene.share.albums import Album

# The longest side of a phone's picture: a 1080-pixel-wide phone shows an upright photo
# at its full width (3:4 → 1080 x 1440). A setting if a phone asks for more.
PHONE_PX: Final = 1440
_DROPPED: Final = "days"  # the list shows each album without its photos


class AlbumReader:
    """Reads the albums, their photos and their pictures for the page."""

    def __init__(self, runtime: Runtime, executor: Executor) -> None:
        """Read through one run's settings and worker pool.

        Args:
            runtime: Settings, mount points and output.
            executor: Makes the pictures.
        """
        self._runtime = runtime
        self._executor = executor
        self._towns: Gazetteer | None = None

    def listing(self) -> Keyed:
        """Every album without its days, and the keys of every album's files.

        Returns:
            `{"albums": [...]}` and the keys.
        """
        albums = album_store(self._runtime).on_disk().albums.albums
        with self._index() as search:
            seen = [self._seen(search, album) for album in albums]
            views = [album_view(each, search.connection, self._town) for each in seen]
        keys = frozenset(slide.key for each in seen for slide in each.picked.slides)
        shown = [{k: v for k, v in view.items() if k != _DROPPED} for view in views]
        return {"albums": shown}, keys

    def album(self, name: str) -> Keyed | None:
        """One album, its photos by day, and the keys of its files.

        Args:
            name: The album's name, whatever its case.

        Returns:
            Its view and keys; None for no album of that name.
        """
        album = album_store(self._runtime).on_disk().albums.named(name)
        if album is None:
            return None
        with self._index() as search:
            seen = self._seen(search, album)
            view = album_view(seen, search.connection, self._town)
        return view, frozenset(slide.key for slide in seen.picked.slides)

    @contextmanager
    def pictures(self, keys: frozenset[int]) -> Iterator[ShowPictures]:
        """The pictures of these files only, the index open meanwhile.

        Args:
            keys: The files that may be shown.

        Yields:
            Their thumbnails, phone-sized pictures and videos.
        """
        previews = self._runtime.previews_dir
        with self._index() as search:
            yield ShowPictures(
                keys,
                Pictures(search, previews, self._executor),
                ScreenJob(PHONE_PX, previews, SQUARE),
                self._executor,
            )

    def source(self, key: int) -> Path | None:
        """The file a key names, for a change of an album.

        Args:
            key: The file's key.

        Returns:
            The file, in the container; None for an unknown key.
        """
        with self._index() as search:
            photo = search.source_of(key)
        return None if photo is None else photo.path

    def _seen(self, search: SearchIndex, album: Album) -> AlbumSeen:
        """An album's photos, oldest first, how many are missing, its chosen cover.

        Args:
            search: The open index.
            album: The album, as saved.

        Returns:
            The album as the page shows it.
        """
        picked = picked_slides(self._runtime, search, Pick(album=album.name))
        cover = cover_key(search.connection, album, self._runtime.mapper)
        return AlbumSeen(album.name, picked, cover)

    def _town(self, point: Point) -> str | None:
        """The town a photo was taken in, near enough to be named (`[tags] town_km`).

        Args:
            point: Its position.

        Returns:
            The town's name, the user's way; None when none is near.
        """
        if self._towns is None:
            names = self._runtime.settings.classify.town_names
            try:
                self._towns = Gazetteer.load().renamed(names)
            except GeoDataError:
                return None  # the days are named without their towns
        town = self._towns.nearest(point)
        if town is None:
            return None
        near = distance_km(point, town.point) <= self._runtime.settings.tags.town_km
        return town.name if near else None

    @contextmanager
    def _index(self) -> Iterator[SearchIndex]:
        """Open the index read-only for one answer.

        Yields:
            The index.

        Raises:
            MountError: No index yet, or one that cannot be read.
        """
        index = self._runtime.index_file
        if index is None or not index.is_file():
            raise MountError(
                _("No index yet: the albums show the photos an audit has seen."),
                _("Run the audit first (Clean, step 1)."),
            )
        try:
            search = SearchIndex.open(index)
        except sqlite3.Error as exc:
            raise unreadable_index(self._runtime, index, exc) from exc
        with search:
            yield search
