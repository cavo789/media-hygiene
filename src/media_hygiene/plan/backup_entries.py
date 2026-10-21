"""The records of `mh backup`'s plan: a file's size and time, a move, an edit (0264)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Robocopy's `/FFT`: times within two seconds are the same time.
SAME_TIME_NS: Final = 2_000_000_000


@dataclass(frozen=True, slots=True)
class Stat:
    """The size and modification time of a file, as a listing gives them."""

    size: int
    mtime_ns: int

    def same(self, other: Stat) -> bool:
        """Tell whether robocopy would take two files for the same.

        Args:
            other: The other file.

        Returns:
            True for the same size and a time within two seconds.
        """
        return (
            self.size == other.size
            and abs(self.mtime_ns - other.mtime_ns) <= SAME_TIME_NS
        )


@dataclass(frozen=True, slots=True)
class Entry:
    """A file, by its path relative to the target."""

    path: str
    stat: Stat


@dataclass(frozen=True, slots=True)
class Move:
    """A target file renamed to the path the PC now gives it."""

    old: Entry  # on the target
    new: str  # the PC's path


@dataclass(frozen=True, slots=True)
class Edit:
    """A file changed on the PC: the target's copy set aside, the PC's copied."""

    old: Entry  # on the target
    new: Entry  # on the PC
