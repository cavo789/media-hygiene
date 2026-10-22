"""What the albums' page reads (0297), and the files it may serve: an album's only."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from contextlib import AbstractContextManager

    from media_hygiene.slideshow.pictures import ShowPictures

type Keyed = tuple[dict[str, object], frozenset[int]]


class AlbumShelf(Protocol):
    """Reads the albums for the page: their views, and the keys of their files."""

    def listing(self) -> Keyed:
        """Every album, without its days; the keys of every album's files."""

    def album(self, name: str) -> Keyed | None:
        """One album with its days, and its keys.

        Args:
            name: The album's name, whatever its case.

        Returns:
            None for an unknown name.
        """

    def pictures(self, keys: frozenset[int]) -> AbstractContextManager[ShowPictures]:
        """The pictures of these files only, the index open meanwhile.

        Args:
            keys: The files that may be shown.

        Returns:
            Their pictures, while the block runs.
        """


class Shown:
    """The keys of the files the albums hold, as last read: the only ones served."""

    __slots__ = ("keys",)

    def __init__(self) -> None:
        """Start with none: the list read first."""
        self.keys: frozenset[int] = frozenset()

    def picked(self, keys: tuple[str, ...]) -> tuple[int, ...]:
        """The keys a page names that belong to an album; the others are dropped.

        Args:
            keys: As the page sent them.

        Returns:
            Those of an album's files.
        """
        return tuple(
            int(key) for key in keys if key.isdigit() and int(key) in self.keys
        )
