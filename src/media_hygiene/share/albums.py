"""`albums.json`: named albums, each a list of references to the user's files (0295).

An album is a logical grouping: nothing is copied, nothing is moved. The file lives in
the reports folder next to `decisions.json`, never in the index (a cache, safe to
delete): an album is the user's choice. Each entry keeps the file's host path, its
SHA-256 and its size, so a file moved since (by `sort`, `undo`, or the user) is found
again by its content. Saved at once (a draft, then renamed), read back by the caller.
Schema 2 (0371): an album may name its cover, by content (SHA-256 and size), so the
cover follows its file wherever the entry does; schema 1 is still read.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.text_files import decode_user_text

if TYPE_CHECKING:
    from pathlib import Path

ALBUMS_FILE: Final = "albums.json"
MAX_NAME: Final = 80
# No double quote: the name is pasted in a command, `slideshow --album "<name>"`.
NAME_PATTERN: Final = r'^[^"\x00-\x1f]+$'
_SHA256: Final = r"^[0-9a-f]{64}$"


class AlbumsError(MediaHygieneError):
    """The albums file cannot be read, or an album asked for does not exist."""


class AlbumEntry(BaseModel):
    """One file of an album: where it was last seen, and what it holds."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str  # as the user knows it (host path)
    sha256: str = Field(pattern=_SHA256)
    size: int = Field(ge=0)
    added: dt.datetime


class AlbumCover(BaseModel):
    """The photo the user chose as an album's cover: its entry's path and content.

    The path tells two identical copies of the album apart; the content finds the
    photo once its path is stale (the entry followed after a move).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str  # as its entry, when chosen

    sha256: str = Field(pattern=_SHA256)
    size: int = Field(ge=0)


class Album(BaseModel):
    """A named album; its files in the order they were added."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=MAX_NAME, pattern=NAME_PATTERN)
    entries: tuple[AlbumEntry, ...] = ()
    cover: AlbumCover | None = None  # None: the tool's choice (0371)

    def cover_entry(self) -> AlbumEntry | None:
        """The entry the chosen cover names, if it is still in the album.

        Returns:
            It; None without a cover, or once taken out.
        """
        cover = self.cover
        if cover is None:
            return None
        same = [
            entry
            for entry in self.entries
            if (entry.sha256, entry.size) == (cover.sha256, cover.size)
        ]
        here = [entry for entry in same if entry.path == cover.path]
        return next(iter(here or same), None)


class AlbumsFile(BaseModel):
    """What `albums.json` holds."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1, 2] = 2  # 1: before the chosen covers (0371), still read
    albums: tuple[Album, ...] = ()

    @field_validator("albums")
    @classmethod
    def _names_once(cls, albums: tuple[Album, ...]) -> tuple[Album, ...]:
        """Refuse two albums of the same name, whatever its case.

        Args:
            albums: The albums.

        Returns:
            Them, unchanged.

        Raises:
            ValueError: A name appears twice.
        """
        names = [same_name(album.name) for album in albums]
        if len(set(names)) != len(names):
            message = "an album name appears twice"
            raise ValueError(message)
        return albums

    def named(self, name: str) -> Album | None:
        """Find an album by its name, whatever its case.

        Args:
            name: The name.

        Returns:
            It, or None.
        """
        wanted = same_name(name)
        return next((a for a in self.albums if same_name(a.name) == wanted), None)


def same_name(name: str) -> str:
    """The form two names are compared in: "Crete 2023" is "crete 2023 ".

    Args:
        name: A name.

    Returns:
        Its comparable form.
    """
    return " ".join(name.split()).casefold()


def read_albums(path: Path) -> AlbumsFile:
    """Read the albums file; none yet is an empty one.

    Args:
        path: The file, in the container.

    Returns:
        Its albums.

    Raises:
        AlbumsError: It cannot be read, or is not an albums file.
    """
    if not path.exists():
        return AlbumsFile()
    tip = _("Put back a copy of it, or move it away to start new albums.")
    try:
        return AlbumsFile.model_validate_json(decode_user_text(path.read_bytes()))
    except OSError as exc:
        message = _("Cannot read the albums file {path}.").format(path=path)
        raise AlbumsError(message, tip) from exc
    except (UnicodeDecodeError, ValidationError) as exc:
        message = _("{path} is not a valid albums file.").format(path=path)
        raise AlbumsError(message, tip) from exc


def write_albums(path: Path, albums: AlbumsFile) -> None:
    """Save the albums file at once: a crash never leaves half a file behind.

    Args:
        path: The file, in the container.
        albums: What to save.
    """
    draft = path.with_name(f".{path.name}.partial")
    draft.write_text(albums.model_dump_json(indent=2) + "\n", encoding="utf-8")
    draft.replace(path)
