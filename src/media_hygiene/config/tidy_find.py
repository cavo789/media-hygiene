"""`config tidy`: the entries of `config.toml` that point at nothing any more (0550).

Each one is judged against facts, never guessed: a folder against the disk (a folder on
a drive that is not mounted is unknown, not missing), a pattern or dates against the
index (an empty index judges nothing). Hand-drawn places and spots set aside are never
proposed: they stay valid for photos to come.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

from media_hygiene.classify.rules.calendar import parse_one_off
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping, Sequence
    from datetime import date

    type Exists = Callable[[str], bool | None]  # host folder → exists; None: unknown

RULES: Final = ("classify", "rules")
CLOCKS: Final = ("classify", "clocks")
PLACE_FOLDERS: Final = ("places", "folders")
FOLDER_ROLES: Final = ("preferred", "protected", "excluded", "backups")


@dataclass(frozen=True, slots=True)
class LibraryFacts:
    """What the index knows: host paths, and each shot's camera and day."""

    paths: tuple[str, ...] = ()
    shots: tuple[tuple[str, date | None], ...] = ()


@dataclass(frozen=True, slots=True)
class StaleEntry:
    """One entry pointing at nothing: where it is, why, ticked by default or not."""

    section: str  # `classify.rules`, `places.folders`, `folders.protected`…
    rank: int  # its rank in that array, from 0
    label: str
    reason: str
    ticked: bool = True


@dataclass(frozen=True, slots=True)
class TidyFindings:
    """The stale entries, and the folders not judged (their drive is not mounted)."""

    stale: tuple[StaleEntry, ...]
    unknown: tuple[str, ...]


def find_stale(
    document: Mapping[str, Any], facts: LibraryFacts, exists: Exists
) -> TidyFindings:
    """List the entries of a parsed `config.toml` that point at nothing.

    Args:
        document: The file, as `tomllib` reads it.
        facts: What the index knows; empty: patterns and dates are not judged.
        exists: Tells whether a host folder exists, None when its drive is unmounted.

    Returns:
        The stale entries, in file order, and the folders not judged.
    """
    unknown: list[str] = []

    def folder(path: str) -> str | None:
        """Why a folder is stale, None when it is not (or not known).

        Args:
            path: The host folder.

        Returns:
            The reason, or None.
        """
        found = exists(path)
        if found is None:
            unknown.append(path)
        return None if found is not False else _("the folder does not exist")

    stale = [
        *_folder_lists(_table(document, "folders"), folder),
        *_place_folders(_array(document, PLACE_FOLDERS), folder),
        *_rules(_array(document, RULES), facts),
        *_clocks(_array(document, CLOCKS), facts),
    ]
    return TidyFindings(tuple(stale), tuple(dict.fromkeys(unknown)))


def _table(document: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = document.get(key)
    return value if isinstance(value, dict) else {}


def _array(document: Mapping[str, Any], where: tuple[str, str]) -> list[Any]:
    value = _table(document, where[0]).get(where[1])
    return value if isinstance(value, list) else []


def _duplicate(rank: int) -> str:
    return _("the same as entry {number}").format(number=rank + 1)


def _folder_lists(
    folders: Mapping[str, Any], folder: Callable[[str], str | None]
) -> Iterator[StaleEntry]:
    for role in FOLDER_ROLES:
        values = folders.get(role)
        seen: dict[str, int] = {}
        for rank, path in enumerate(values if isinstance(values, list) else []):
            key = str(path).casefold()
            reason = _duplicate(seen[key]) if key in seen else folder(str(path))
            seen.setdefault(key, rank)
            if reason:
                yield StaleEntry(f"folders.{role}", rank, str(path), reason)


def _place_folders(
    rows: Sequence[Any], folder: Callable[[str], str | None]
) -> Iterator[StaleEntry]:
    seen: dict[str, int] = {}
    for rank, row in enumerate(rows):
        path = str(row.get("folder", "")) if isinstance(row, dict) else ""
        key = path.casefold()
        reason = _duplicate(seen[key]) if key in seen else folder(path)
        seen.setdefault(key, rank)
        if reason:
            yield StaleEntry(".".join(PLACE_FOLDERS), rank, path, reason)


def _rules(rows: Sequence[Any], facts: LibraryFacts) -> Iterator[StaleEntry]:
    seen: list[Any] = []
    for rank, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        label = str(row.get("name", ""))
        if row in seen:
            yield StaleEntry(".".join(RULES), rank, label, _duplicate(seen.index(row)))
        elif (found := _rule_reason(row, facts)) is not None:
            reason, ticked = found
            yield StaleEntry(".".join(RULES), rank, label, reason, ticked)
        seen.append(row)


def _rule_reason(
    row: Mapping[str, Any], facts: LibraryFacts
) -> tuple[str, bool] | None:
    match, pattern = row.get("match"), str(row.get("pattern", ""))
    if not facts.paths:
        return None  # an empty index judges nothing
    if match == "path" and not _searched(pattern, facts.paths):
        return _("no indexed path matches '{pattern}'").format(pattern=pattern), True
    cameras = tuple(camera for camera, _day in facts.shots)
    if match == "camera" and not _searched(pattern, cameras):
        return _("no indexed camera matches '{pattern}'").format(pattern=pattern), True
    if match == "date_range" and not _dated(str(row.get("dates", "")), facts, None):
        # Written before an import, maybe: shown, never ticked by default.
        return _("no indexed photo was taken on these dates"), False
    return None


def _clocks(rows: Sequence[Any], facts: LibraryFacts) -> Iterator[StaleEntry]:
    for rank, row in enumerate(rows):
        if not facts.paths or not isinstance(row, dict):
            continue
        camera, dates = str(row.get("camera", "")), str(row.get("dates", ""))
        if not _dated(dates, facts, camera):
            reason = _("no photo of this camera was taken on these dates")
            yield StaleEntry(".".join(CLOCKS), rank, f"{camera} {dates}", reason)


def _searched(pattern: str, texts: Sequence[str]) -> bool:
    try:
        compiled = re.compile(pattern)
    except re.error:
        return True  # refused at load time anyway: not ours to judge
    return any(compiled.search(text) for text in texts)


def _dated(dates: str, facts: LibraryFacts, camera: str | None) -> bool:
    try:
        span = parse_one_off(dates)
        compiled = re.compile(camera) if camera else None
    except ValueError, re.error:
        return True
    return any(
        day is not None
        and span.contains(day)
        and (compiled is None or compiled.search(shot))
        for shot, day in facts.shots
    )
