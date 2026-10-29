r"""Which files of a phone `import --phone` copies, and why it leaves the others (0219).

A phone plugged in over USB has no drive letter: Docker cannot see it, `mh.ps1` can.
`mh` lists the phone's `DCIM` (relative path, size, modified date in UTC), pipes the
list to `phone-plan`, which compares it with what only the container knows: the
index (the library), the journals (what the user set aside on purpose) and the
destination folder. Matched by name (case ignored) and size only (no content to hash);
each file gets a case and its reason, one line each, reused to free the phone (0248).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from datetime import datetime

# A file of the phone: its name, case folded, and its size.
type NameKey = tuple[str, int]

# The hidden command `mh import --phone` pipes the listing to: plumbing, no page (0219).
PHONE_PLAN: Final = "phone-plan"
# Freeing the phone (0248): its page, the proof and its journal.
PHONE_REVIEW, PHONE_PROVE, PHONE_DONE = "phone-review", "phone-prove", "phone-done"
SEPARATOR: Final = "\t"
_FIELDS: Final = 3  # relative path, size, modified date
_PARENT, _BOM = "..", "﻿"
# Inside a line of the plan, a tab would start another field.
_SPACE: Final = " "


class PhoneCase(StrEnum):
    """What `import --phone` does with a phone's file, the first word of its line."""

    NEW = "new"  # copied
    LIBRARY = "library"  # the library holds a file of that name and size
    SET_ASIDE = "set-aside"  # the journals remember it as set aside on purpose
    DESTINATION = "destination"  # the destination folder holds it already
    OLDER = "older"  # new, but before `--since`: left on the phone (0476)


class AsideState(StrEnum):
    """Where it is now: in a quarantine, purged, or deleted (`review --gone`, 0377)."""

    QUARANTINE = "quarantine"
    PURGED = "purged"
    WAITING = "waiting"


@dataclass(frozen=True, slots=True)
class PhoneFile:
    """A file of the phone, as `mh` listed it: below `DCIM`, `/` between folders."""

    path: PurePosixPath
    size: int
    modified: str  # `System.DateModified`, UTC, as the phone said it

    @property
    def key(self) -> NameKey:
        """Its name, case ignored, and its size: all the phone tells of it.

        Returns:
            The key.
        """
        return (self.path.name.casefold(), self.size)


@dataclass(frozen=True, slots=True)
class SetAside:
    """A file of that name and size set aside by a choice: which run, when, why."""

    run_id: str
    at: datetime
    action: str
    state: AsideState
    host_path: str = ""  # where it lay: its copy in the quarantine mirrors it (0256)
    purged: datetime | None = None  # when its quarantine was purged, if recorded


def _empty[V]() -> Mapping[NameKey, V]:
    """An empty, read-only mapping.

    Returns:
        It.
    """
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class Known:
    """What the container knows of the files named like the phone's, of that size."""

    library: Mapping[NameKey, str] = field(default_factory=_empty)  # host path
    set_aside: Mapping[NameKey, SetAside] = field(default_factory=_empty)
    destination: Mapping[NameKey, str] = field(default_factory=_empty)  # relative


@dataclass(frozen=True, slots=True)
class Verdict:
    """A file of the phone, its case, and its reason (which file, which run)."""

    file: PhoneFile
    case: PhoneCase
    reason: tuple[str, ...] = ()

    def line(self) -> str:
        """Write the verdict as `mh` reads it: the case, the path, size, date, reason.

        Returns:
            One line, its fields separated by tabs, without the line end.
        """
        fields = (
            self.case.value,
            self.file.path.as_posix(),
            str(self.file.size),
            self.file.modified,
            *self.reason,
        )
        return SEPARATOR.join(text.replace(SEPARATOR, _SPACE) for text in fields)


def read_listing(lines: Iterable[str]) -> tuple[tuple[PhoneFile, ...], int]:
    """Read the phone's listing: one `path<TAB>size<TAB>date` line per file.

    Args:
        lines: The lines `mh` piped in.

    Returns:
        The files, in the order given, each path once; and the count of lines
        skipped (not three fields, a size that is no number, a path leaving `DCIM`).
    """
    files: dict[PurePosixPath, PhoneFile] = {}
    skipped = 0
    for raw in lines:
        text = raw.strip().lstrip(_BOM)
        if not text:
            continue
        file = file_of(text.split(SEPARATOR))
        if file is None:
            skipped += 1
            continue
        files.setdefault(file.path, file)
    return tuple(files.values()), skipped


def file_of(fields: list[str]) -> PhoneFile | None:
    """Read one line of the listing.

    Args:
        fields: Its fields.

    Returns:
        The file, or None when the line is not one.
    """
    if len(fields) != _FIELDS or not fields[1].isdigit():
        return None
    path = PurePosixPath(fields[0].replace("\\", "/"))
    if not path.name or path.is_absolute() or _PARENT in path.parts:
        return None
    return PhoneFile(path, int(fields[1]), fields[2])


def decide(files: Iterable[PhoneFile], known: Known) -> tuple[Verdict, ...]:
    """Give each file of the phone its case: the library first, then the journals.

    Args:
        files: The files of the phone.
        known: What the index, the journals and the destination hold.

    Returns:
        A verdict per file, in the order given.
    """
    return tuple(_verdict(file, known) for file in files)


def _verdict(file: PhoneFile, known: Known) -> Verdict:
    """Give one file its case and its reason.

    Args:
        file: A file of the phone.
        known: What the container knows.

    Returns:
        Its verdict.
    """
    key = file.key
    if (held := known.library.get(key)) is not None:
        return Verdict(file, PhoneCase.LIBRARY, (held,))
    if (aside := known.set_aside.get(key)) is not None:
        purged = aside.purged.isoformat() if aside.purged is not None else ""
        reason = (aside.run_id, aside.state.value, aside.at.isoformat(), aside.action)
        return Verdict(file, PhoneCase.SET_ASIDE, (*reason, aside.host_path, purged))
    if (there := known.destination.get(key)) is not None:
        return Verdict(file, PhoneCase.DESTINATION, (there,))
    return Verdict(file, PhoneCase.NEW)
