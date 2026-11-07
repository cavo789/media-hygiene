"""What a page's keys name: a file of the index, or a shot of the review (0295)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.search.aside_filter import Kept
from media_hygiene.search.reading import read_query

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.search.aside_filter import AsideFilter
    from media_hygiene.search.found_narrow import FoundNarrow
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.share.album_api import AlbumAsked


@dataclass(frozen=True, slots=True)
class SearchPicker:
    """`library` and `browse`: keys of the index, or every file a search finds."""

    index: SearchIndex
    aside: AsideFilter | None = None  # drops the files set aside (0518)
    narrowing: FoundNarrow | None = None  # the page's album, place (0602, 0642)

    def files(self, asked: AlbumAsked) -> Kept:
        """The files a request names, those set aside left out but to take out.

        Args:
            asked: The request.

        Returns:
            Them, in the container; unknown keys left out.
        """
        if asked.all:
            query = read_query(self.index, asked.search.query())
            if self.narrowing is not None:
                query = self.narrowing.query(query, asked.search)
            picked = tuple(photo.path for photo in self.index.versions(query))
        else:
            found = (
                self.index.source_of(int(key)) for key in asked.keys if key.isdigit()
            )
            picked = tuple(photo.path for photo in found if photo is not None)
        if self.aside is None or asked.action == "remove":
            return Kept(picked)
        return self.aside.keep(picked)


@dataclass(frozen=True, slots=True)
class KeyPicker:
    """The burst review: the keys of its shots, as its previews name them."""

    source: Callable[[str], Path | None]
    aside: AsideFilter | None = None  # drops the shots set aside (0518)

    def files(self, asked: AlbumAsked) -> Kept:
        """The files a request names, those set aside left out but to take out.

        Args:
            asked: The request.

        Returns:
            Them, in the container; unknown keys left out.
        """
        found = (self.source(key) for key in asked.keys)
        picked = tuple(path for path in found if path is not None)
        if self.aside is None or asked.action == "remove":
            return Kept(picked)
        return self.aside.keep(picked)
