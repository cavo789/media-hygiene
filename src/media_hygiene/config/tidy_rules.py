"""`config tidy`: the rules and clock corrections the index proves stale.

A pattern or dates are judged against the index (an empty index judges nothing). A
`path` rule is stale when no indexed path matches it, and superseded (0693) when every
file it matches already sits in a folder the user named: `existing_folder` would keep
that folder, the rule (read first) moves its files out of it. A rule aimed at a
root the index never covered is left alone (`tidy_roots`). A rule renaming a
folder on purpose looks the same, so a superseded rule is shown, never ticked by
default.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.rules.calendar import parse_one_off
from media_hygiene.config.tidy_roots import aimed_root, covered
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence
    from datetime import date
    from typing import Any

RULES: Final = ("classify", "rules")
CLOCKS: Final = ("classify", "clocks")


class OptIn(StrEnum):
    """The stale entries shown but ticked only on request."""

    DATES = "dates"  # a date_range with no photo: maybe written before an import
    SUPERSEDED = "superseded"  # a path rule whose files sit in folders the user named


@dataclass(frozen=True, slots=True)
class LibraryFacts:
    """What the index knows: host paths, each shot's camera and day, named folders.

    `named`: the host paths whose folder carries a name the user gave (not a date, not
    a device or generic folder), as `existing_folder` reads it.
    """

    paths: tuple[str, ...] = ()
    shots: tuple[tuple[str, date | None], ...] = ()
    named: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class StaleEntry:
    """One stale entry: where it is, why, what ticks it (None: ticked by default)."""

    section: str  # `classify.rules`, `places.folders`, `folders.protected`…
    rank: int  # its rank in that array, from 0
    label: str
    reason: str
    opt_in: OptIn | None = None

    @property
    def ticked(self) -> bool:
        """Whether `--apply` removes it without being asked to.

        Returns:
            True when no opt-in is needed.
        """
        return self.opt_in is None


def duplicate(rank: int) -> str:
    """The reason of an entry repeating another one.

    Args:
        rank: The other entry's rank, from 0.

    Returns:
        The reason.
    """
    return _("the same as entry {number}").format(number=rank + 1)


def stale_rules(rows: Sequence[Any], facts: LibraryFacts) -> Iterator[StaleEntry]:
    """The rules repeated, or that the index proves stale.

    Args:
        rows: `[[classify.rules]]`, as `tomllib` reads it.
        facts: What the index knows.

    Yields:
        The stale rules, in file order.
    """
    seen: list[Any] = []
    for rank, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        label = str(row.get("name", ""))
        if row in seen:
            yield StaleEntry(".".join(RULES), rank, label, duplicate(seen.index(row)))
        elif (found := _rule_reason(row, facts)) is not None:
            reason, opt_in = found
            yield StaleEntry(".".join(RULES), rank, label, reason, opt_in)
        seen.append(row)


def _rule_reason(
    row: Mapping[str, Any], facts: LibraryFacts
) -> tuple[str, OptIn | None] | None:
    match, pattern = row.get("match"), str(row.get("pattern", ""))
    if not facts.paths:
        return None  # an empty index judges nothing
    if match == "path":
        return _path_reason(pattern, facts)
    cameras = tuple(camera for camera, _day in facts.shots)
    if match == "camera" and not _found(pattern, cameras):
        return _("no indexed camera matches '{pattern}'").format(pattern=pattern), None
    if match == "date_range" and not _dated(str(row.get("dates", "")), facts, None):
        return _("no indexed photo was taken on these dates"), OptIn.DATES
    return None


def _path_reason(pattern: str, facts: LibraryFacts) -> tuple[str, OptIn | None] | None:
    try:
        compiled = re.compile(pattern)
    except re.error:
        return None  # refused at load time anyway: not ours to judge
    matched = [path for path in facts.paths if compiled.search(path)]
    if not matched:
        root = aimed_root(pattern)
        if root is not None and not covered(root, facts.paths):
            return None  # aimed at a root the index never covered (0751)
        return _("no indexed path matches '{pattern}'").format(pattern=pattern), None
    if all(path in facts.named for path in matched):
        reason = _(
            "its {count} files already sit in folders you named: sort would move "
            "them out"
        ).format(count=len(matched))
        return reason, OptIn.SUPERSEDED
    return None


def stale_clocks(rows: Sequence[Any], facts: LibraryFacts) -> Iterator[StaleEntry]:
    """The clock corrections no indexed photo of their camera needs.

    Args:
        rows: `[[classify.clocks]]`, as `tomllib` reads it.
        facts: What the index knows.

    Yields:
        The stale corrections, in file order.
    """
    for rank, row in enumerate(rows):
        if not facts.paths or not isinstance(row, dict):
            continue
        camera, dates = str(row.get("camera", "")), str(row.get("dates", ""))
        if not _dated(dates, facts, camera):
            reason = _("no photo of this camera was taken on these dates")
            yield StaleEntry(".".join(CLOCKS), rank, f"{camera} {dates}", reason)


def _found(pattern: str, texts: Sequence[str]) -> bool:
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
