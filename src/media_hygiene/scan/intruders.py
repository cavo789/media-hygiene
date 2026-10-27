"""Intruder files: what lies in the photo folders and is neither media nor companion.

A zip, a docx or a pdf copied among the family photos (0410). The walk sees them
anyway (`os.scandir` lists every entry, the index keeps every listing): telling the
user costs no extra disk read. Companions (`[scan] companions`: sidecars, Takeout
`.json`, `Thumbs.db`, `desktop.ini`...) are never intruders.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.paths.host_paths import is_within

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

# What follows a photo or a folder of photos: never an intruder (`[scan] companions`).
DEFAULT_COMPANIONS: Final = (
    ".xmp",
    ".aae",
    ".thm",
    ".json",
    "thumbs.db",
    "desktop.ini",
    ".ds_store",
    ".picasa.ini",
    "picasa.ini",
    ".nomedia",
    ".lrv",
    ".srt",
)
NO_EXTENSION: Final = "(none)"


@dataclass(frozen=True, slots=True)
class Intruder:
    """A file of a photo folder that is neither a photo, a video nor a companion."""

    path: Path
    size: int
    mtime_ns: int

    @property
    def extension(self) -> str:
        """Its extension, lowercase with its dot, or `(none)`.

        Returns:
            E.g. `.zip`.
        """
        return self.path.suffix.casefold() or NO_EXTENSION


def outside(
    intruders: Iterable[Intruder], folders: Iterable[Path]
) -> tuple[Intruder, ...]:
    """Leave out the intruder files of some folders (protected, backups): never moved.

    Args:
        intruders: The files.
        folders: Container paths.

    Returns:
        The files lying in none of them.
    """
    kept = tuple(folders)
    return tuple(
        item
        for item in intruders
        if not any(is_within(item.path, folder) for folder in kept)
    )


def is_companion(name: str, companions: Iterable[str]) -> bool:
    """Tell whether a file name is a companion: a whole name or an extension listed.

    Args:
        name: A file name, e.g. `Thumbs.db` or `IMG_1.jpg.json`.
        companions: Names and extensions (with their dot), lowercase.

    Returns:
        True when its whole name, or its end for an entry starting with a dot, matches.
    """
    folded = name.casefold()
    return any(
        folded == entry or (entry.startswith(".") and folded.endswith(entry))
        for entry in companions
    )


@dataclass(frozen=True, slots=True)
class Tally:
    """How many intruder files, and how many bytes, per key (extension or folder)."""

    count: Counter[str]
    size: Counter[str]

    def heaviest(self, limit: int) -> list[tuple[str, int, int]]:
        """The heaviest keys first.

        Args:
            limit: How many keys at most.

        Returns:
            Each key, its file count and its bytes.
        """
        keys = sorted(self.size, key=lambda key: (-self.size[key], key))[:limit]
        return [(key, self.count[key], self.size[key]) for key in keys]


def tally(intruders: Iterable[Intruder], *, by_folder: bool = False) -> Tally:
    """Count intruder files and their bytes, per extension or per folder.

    Args:
        intruders: The files.
        by_folder: Per folder (its path) instead of per extension.

    Returns:
        The counts and the bytes per key.
    """
    count: Counter[str] = Counter()
    size: Counter[str] = Counter()
    for item in intruders:
        key = str(item.path.parent) if by_folder else item.extension
        count[key] += 1
        size[key] += item.size
    return Tally(count, size)
