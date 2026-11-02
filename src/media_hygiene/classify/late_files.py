"""Photos arriving later in an event's days (0558): proposed, never moved blindly.

A spouse's phone, a USB stick found, a friend's photos: files of the index dated in a
remembered event's days (a `date_range` rule of `config.toml`), outside any event
folder `YYYY/YYYY-MM/<name>` and not refused. Each one is ranked by its camera: the
event's own (*probably*), another one (*during, but elsewhere*), the camera of
**another** event of the same days (proposed there instead), none in its EXIF (asked:
received, a scan). No file list is stored: the index and the rules say it all.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.event_files import read_refused
from media_hygiene.classify.found_folders import event_folder_of, moment
from media_hygiene.classify.rules.calendar import parse_one_off
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.errors import ConfigError

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Mapping, Sequence
    from datetime import date
    from pathlib import Path

    from media_hygiene.config.classify_rules import ClassifyRule

_ROWS: Final = (
    "SELECT rowid, path, media_date, camera, full_digest FROM files"
    " WHERE media_date IS NOT NULL"
)


class Likely(StrEnum):
    """How a late file fits an event, from its camera."""

    PROBABLY = "probably"  # the event's camera, or an event of no camera
    ELSEWHERE = "elsewhere"  # another camera: during, but elsewhere
    OTHER = "other"  # the camera of another event of the same days
    ASK = "ask"  # no camera in its EXIF: never guessed


@dataclass(frozen=True, slots=True)
class LateFile:
    """One file of an event's days, not in its folder."""

    key: int
    digest: str  # its content id; empty before the index read its bytes
    likely: Likely
    other: str = ""  # Likely.OTHER: the other event's rule name


@dataclass(frozen=True, slots=True)
class LateEvent:
    """An event and the files arrived later in its days."""

    rule: ClassifyRule
    files: tuple[LateFile, ...]


@dataclass(frozen=True, slots=True)
class _Row:
    """A dated file outside any event folder."""

    key: int
    day: date
    camera: str  # casefolded; empty without one
    digest: str


def refused_by_event(
    config_dir: Path, rules: Sequence[ClassifyRule]
) -> dict[str, frozenset[str]]:
    """The refused content ids of every event, by rule name (classify skips them).

    Args:
        config_dir: The folder of `config.toml`.
        rules: The rules.

    Returns:
        Rule name → ids; an event whose file cannot be read refuses nothing.
    """
    refused: dict[str, frozenset[str]] = {}
    for rule in rules:
        if rule.match is not RuleMatch.DATE_RANGE or not rule.file:
            continue
        try:
            refused[rule.name] = read_refused(config_dir, rule)
        except ConfigError:
            continue
    return refused


def late_files(
    connection: sqlite3.Connection,
    rules: Sequence[ClassifyRule],
    refused: Mapping[str, frozenset[str]],
) -> list[LateEvent]:
    """Every event with files of its days not yet in an event folder.

    Args:
        connection: The index.
        rules: The rules of `config.toml`.
        refused: Rule name → the content ids it never takes.

    Returns:
        The events having some, in the file's order.
    """
    events = [rule for rule in rules if rule.match is RuleMatch.DATE_RANGE]
    rows = _loose_rows(connection)
    found: list[LateEvent] = []
    for rule in events:
        period = parse_one_off(rule.dates)
        never = refused.get(rule.name, frozenset())
        files = tuple(
            _ranked(row, rule, events)
            for row in rows
            if period.contains(row.day) and row.digest not in never
        )
        if files:
            found.append(LateEvent(rule, files))
    return found


def _loose_rows(connection: sqlite3.Connection) -> list[_Row]:
    """The dated files of the index outside any event folder.

    Args:
        connection: The index.

    Returns:
        Them.
    """
    rows: list[_Row] = []
    for key, path, written, camera, digest in connection.execute(_ROWS):
        if event_folder_of(str(path)) is not None:
            continue
        when = moment(written)
        if when is None:
            continue
        name = str(camera or "").strip().casefold()
        rows.append(_Row(int(key), when.date(), name, str(digest or "")))
    return rows


def _ranked(row: _Row, rule: ClassifyRule, events: Sequence[ClassifyRule]) -> LateFile:
    """How one file fits an event.

    Args:
        row: The file.
        rule: The event.
        events: Every event: another one of its days may own its camera.

    Returns:
        The file, ranked.
    """
    if not row.camera:
        return LateFile(row.key, row.digest, Likely.ASK)
    own = {device.casefold() for device in rule.devices}
    if not own or row.camera in own:
        return LateFile(row.key, row.digest, Likely.PROBABLY)
    for other in events:
        if other.name == rule.name or not parse_one_off(other.dates).contains(row.day):
            continue
        if row.camera in {device.casefold() for device in other.devices}:
            return LateFile(row.key, row.digest, Likely.OTHER, other.name)
    return LateFile(row.key, row.digest, Likely.ELSEWHERE)
