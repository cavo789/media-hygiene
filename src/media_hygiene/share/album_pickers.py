"""What a page's keys name: a file of the index, or a shot of the review (0295)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.search.reading import read_query

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.share.album_api import AlbumAsked


@dataclass(frozen=True, slots=True)
class SearchPicker:
    """`search` and `browse`: keys of the index, or every file a search finds."""

    index: SearchIndex

    def files(self, asked: AlbumAsked) -> tuple[Path, ...]:
        """The files a request names.

        Args:
            asked: The request.

        Returns:
            Them, in the container; unknown keys left out.
        """
        if asked.all:
            return tuple(
                photo.path
                for photo in self.index.versions(
                    read_query(self.index, asked.search.query())
                )
            )
        found = (self.index.source_of(int(key)) for key in asked.keys if key.isdigit())
        return tuple(photo.path for photo in found if photo is not None)


@dataclass(frozen=True, slots=True)
class KeyPicker:
    """The burst review: the keys of its shots, as its previews name them."""

    source: Callable[[str], Path | None]

    def files(self, asked: AlbumAsked) -> tuple[Path, ...]:
        """The files a request names.

        Args:
            asked: The request.

        Returns:
            Them, in the container; unknown keys left out.
        """
        found = (self.source(key) for key in asked.keys)
        return tuple(path for path in found if path is not None)
