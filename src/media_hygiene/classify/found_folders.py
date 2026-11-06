"""The events the user already sorted by hand, found in the index (0557).

A folder `YYYY/YYYY-MM/<name>` (anywhere below a root, as `shape_in` reads it) whose
name means something (not a date, a device, a person's) is an event of theirs: its
period runs from its first to its last dated file, its cameras are its files'. No disk
walk and no file list: the index's rows, grouped by folder. A folder whose dates leave
a gap longer than `merge_gap_hours` (`Prints jan10`) is a batch, told apart.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.convention import Place, shape_of
from media_hygiene.classify.hand_days import SIDECAR_DAY, known, ready
from media_hygiene.classify.own_events import one_moment

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable

    from media_hygiene.classify.folders import FolderRules

_ROWS: Final = (
    f"SELECT rowid, path, media_date, camera, full_digest, {SIDECAR_DAY} FROM files"  # noqa: S608
)
_DAY: Final = slice(0, 10)  # `YYYY:MM:DD` (EXIF) or `YYYY-MM-DD` (ISO)
_TIME: Final = slice(10, 19)  # ` HH:MM:SS` or `THH:MM:SS`
_BELOW_MONTH: Final = 3  # year, month, the event's name


@dataclass(frozen=True, slots=True)
class FoundFolder:
    """One event folder of the index: its name, period, cameras and files."""

    folder: str  # container path of `YYYY/YYYY-MM/<name>`
    name: str
    days: tuple[date, ...]  # every day of a dated file, sorted
    devices: tuple[str, ...]
    keys: tuple[int, ...]  # its files' index keys, sorted
    ids: frozenset[str]  # content ids (SHA-256) of its files
    one_moment: bool  # False: a batch, never proposed


@dataclass(slots=True)
class _Gathered:
    """What a folder's rows say, while reading them."""

    keys: list[int]
    when: list[datetime]
    cameras: set[str]
    ids: set[str]


def event_folder_of(path: str) -> tuple[str, str] | None:
    """The `YYYY/YYYY-MM/<name>` folder holding a file, and that name.

    Args:
        path: A file's container path.

    Returns:
        The folder and its name; None outside such a folder.
    """
    parts = PurePosixPath(path).parent.parts
    for index in range(len(parts) - 2):
        if shape_of(parts[index:]).place is Place.EVENT:
            end = index + _BELOW_MONTH
            return str(PurePosixPath(*parts[:end])), parts[end - 1]
    return None


def moment(written: object) -> datetime | None:
    """The date and time the index holds for a file.

    Args:
        written: `media_date`: EXIF `YYYY:MM:DD HH:MM:SS` or ISO.

    Returns:
        It, without time zone; None when unreadable.
    """
    text = str(written)
    day = text[_DAY].replace(":", "-")
    clock = text[_TIME].strip().removeprefix("T")
    try:
        return datetime.fromisoformat(f"{day} {clock}" if clock else day)
    except ValueError:
        return None


def found_folders(
    connection: sqlite3.Connection, rules: FolderRules, gap_hours: float
) -> list[FoundFolder]:
    """Every event folder the index holds files of, by folder.

    Args:
        connection: The index.
        rules: What folder names mean (dates, devices, people).
        gap_hours: `[classify] merge_gap_hours`.

    Returns:
        The folders of a meaningful name with at least one dated file, by path.
    """
    gathered: dict[tuple[str, str], _Gathered] = defaultdict(
        lambda: _Gathered([], [], set(), set())
    )
    for key, path, written, camera, digest, hand in ready(connection).execute(_ROWS):
        place = event_folder_of(str(path))
        if place is None:
            continue
        held = gathered[place]
        held.keys.append(int(key))
        own = moment(written) if written else None
        if (when := known(own, hand and moment(hand))) is not None:
            held.when.append(when)
        if camera and str(camera).strip():
            held.cameras.add(str(camera).strip())
        if digest:
            held.ids.add(str(digest))
    return [
        _found((folder, name), held, gap_hours)
        for (folder, name), held in sorted(gathered.items())
        if held.when and _meaningful(name, rules)
    ]


def _meaningful(name: str, rules: FolderRules) -> bool:
    """Tell a name of an event: not a date, generic, a device's or a person's.

    Args:
        name: The folder's name.
        rules: What names mean.

    Returns:
        True for an event's name.
    """
    label = rules.label(name)
    return label is not None and not rules.of_person((label,))


def _found(place: tuple[str, str], held: _Gathered, gap_hours: float) -> FoundFolder:
    """One folder, its rows read.

    Args:
        place: Its path and name.
        held: Its rows.
        gap_hours: `merge_gap_hours`.

    Returns:
        It.
    """
    folder, name = place
    return FoundFolder(
        folder=folder,
        name=name,
        days=tuple(sorted({when.date() for when in held.when})),
        devices=tuple(sorted(held.cameras)),
        keys=tuple(sorted(held.keys)),
        ids=frozenset(held.ids),
        one_moment=one_moment(held.when, gap_hours),
    )


def days_of(folders: Iterable[FoundFolder]) -> frozenset[date]:
    """Every day of folders.

    Args:
        folders: Folders.

    Returns:
        Their days.
    """
    return frozenset(day for folder in folders for day in folder.days)
