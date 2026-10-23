"""The videos worth lightening, read from the index alone: nothing is decoded to list.

A video is a candidate when the audit described it (codec, size in pixels, length) and
its codec is one of `[shrink] codecs`, or it spends more than `bits_per_pixel` bits per
pixel and per frame. Never one in a protected, excluded or backup folder, one outside
the folders asked, nor one remembered as not worth it (same path, size and date). The
size after is an estimate (`estimate`): only the encoding tells.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.filters import media_kind
from media_hygiene.shrink.estimate import estimated_size

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.config.shrink_settings import ShrinkSettings

FILES: Final = "SELECT path, size, mtime_ns, metadata FROM files"
type FileKey = tuple[str, int, int]  # path, size, mtime_ns: one version of a file
_SHORTEST: Final = 1.0  # seconds: a shorter clip is not worth an encoding
_BITS_PER_BYTE: Final = 8


@dataclass(frozen=True, slots=True)
class Look:
    """What a video shows: its length, size in pixels and frame rate."""

    duration: float
    width: int
    height: int
    fps: float

    @property
    def per_second(self) -> float:
        """The pixels it shows each second.

        Returns:
            Width times height times frames per second.
        """
        return self.width * self.height * self.fps


@dataclass(frozen=True, slots=True)
class Candidate:
    """A video worth lightening, as the index describes it."""

    path: Path
    size: int
    mtime_ns: int
    codec: str
    look: Look
    estimated: int  # bytes after, estimated

    @property
    def duration(self) -> float:
        """Its length.

        Returns:
            Seconds.
        """
        return self.look.duration

    @property
    def key(self) -> FileKey:
        """The version of the file the index described.

        Returns:
            Its path, size and modification time.
        """
        return (str(self.path), self.size, self.mtime_ns)


@dataclass(frozen=True, slots=True)
class Selection:
    """Which videos may be chosen: the rules, the folders, what was tried before."""

    settings: ShrinkSettings
    within: tuple[Path, ...]  # the mounted folders, or those asked with `--folder`
    untouchable: tuple[Path, ...] = ()  # protected, excluded and backup folders
    not_worth: frozenset[FileKey] = frozenset()
    lighter: bool = False  # `--lighter`: at most `lighter_lines` lines


def candidates(
    rows: Iterable[tuple[str, int, int, str | None]], selection: Selection
) -> tuple[Candidate, ...]:
    """Choose the videos worth lightening, the largest gain first.

    Args:
        rows: The path, size, modification time and metadata of each indexed file.
        selection: The rules and the folders.

    Returns:
        The candidates.
    """
    found = (_candidate(row, selection) for row in rows)
    chosen = [candidate for candidate in found if candidate is not None]
    return tuple(sorted(chosen, key=lambda c: (c.estimated - c.size, str(c.path))))


def _candidate(
    row: tuple[str, int, int, str | None], selection: Selection
) -> Candidate | None:
    """Describe one file as a candidate, if it is one.

    Args:
        row: Its path, size, modification time and metadata.
        selection: The rules and the folders.

    Returns:
        The candidate, or None.
    """
    text, size, mtime_ns, metadata = row
    if metadata is None or not _eligible(Path(text), (text, size, mtime_ns), selection):
        return None
    facts = json.loads(metadata)
    look = _look(facts)
    if look is None:
        return None
    codec = str(facts.get("codec") or "")
    rate = facts.get("bit_rate") or size * _BITS_PER_BYTE / look.duration
    rules = selection.settings
    if codec not in rules.codecs and rate / look.per_second <= rules.bits_per_pixel:
        return None
    lines = rules.lighter_lines if selection.lighter else None
    picture = (look.width, look.height, look.fps)
    after = estimated_size(look.duration, picture, lines)
    return Candidate(Path(text), size, mtime_ns, codec, look, after)


def _eligible(path: Path, key: FileKey, selection: Selection) -> bool:
    """Tell whether a file may be lightened, whatever it holds.

    Args:
        path: The file.
        key: Its path, size and modification time.
        selection: The folders, and what was tried before.

    Returns:
        True for a video in a folder asked, not untouchable, not found not worth it.
    """
    return (
        media_kind(path) is MediaKind.VIDEO
        and any(is_within(path, folder) for folder in selection.within)
        and not any(is_within(path, folder) for folder in selection.untouchable)
        and key not in selection.not_worth
    )


def _look(facts: dict[str, object]) -> Look | None:
    """Read the length, size in pixels and frame rate of a video.

    Args:
        facts: Its metadata, as the index stores it.

    Returns:
        Them, or None when one is missing or makes no sense.
    """
    duration, width, height = (
        facts.get("duration"),
        facts.get("width"),
        facts.get("height"),
    )
    if not isinstance(duration, int | float) or duration < _SHORTEST:
        return None
    if not isinstance(width, int) or not isinstance(height, int) or not width * height:
        return None
    fps = _fps(facts.get("frame_rate"))
    return None if fps is None else Look(float(duration), width, height, fps)


def _fps(value: object) -> float | None:
    """Read a frame rate written as ffprobe does, `30000/1001` or `25`.

    Args:
        value: The frame rate.

    Returns:
        Frames per second, or None when unknown or zero.
    """
    try:
        rate = Fraction(str(value))
    except ValueError, ZeroDivisionError:
        return None
    return float(rate) if rate > 0 else None
