"""The Summary sheet of the inventory: counts per kind, year, camera, format, state.

Counted while the rows stream to the Files sheet: the index is read once.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.report.inventory_labels import (
    camera_of,
    format_of,
    integrity_label,
    kind_label,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.report.inventory_entries import Entry


class Topic(IntEnum):
    """What a count is about, in the order of the sheet."""

    KIND = 1
    YEAR = 2
    CAMERA = 3
    FORMAT = 4
    INTEGRITY = 5
    DATE = 6
    PLACE = 7
    DUPLICATES = 8


# Topics listed in the order of their values (years), not by count.
_IN_VALUE_ORDER = frozenset({Topic.YEAR})


@dataclass(frozen=True, slots=True)
class InventorySummary:
    """Counts by topic and value, filled entry by entry."""

    counts: Counter[tuple[Topic, str]] = field(default_factory=Counter)
    groups: set[int] = field(default_factory=set)

    def add(self, entry: Entry) -> None:
        """Count one file.

        Args:
            entry: The file.
        """
        dated = entry.dated()
        metadata = entry.metadata
        located = metadata is not None and metadata.located
        shared = entry.shared()
        topics = (
            (Topic.KIND, kind_label(entry.kind)),
            (Topic.YEAR, str(dated[0].year) if dated else _("no date")),
            (Topic.CAMERA, camera_of(entry) or _("unknown")),
            (Topic.FORMAT, format_of(entry)),
            (Topic.INTEGRITY, integrity_label(entry)),
            (Topic.DATE, _("with a date") if dated else _("without a date")),
            (Topic.PLACE, _("with GPS") if located else _("without GPS")),
        )
        self.counts.update(topics)
        if shared is not None:
            self.counts[Topic.DUPLICATES, _("files with an identical copy")] += 1
            self.groups.add(shared.group)

    @property
    def files(self) -> int:
        """Count the files added.

        Returns:
            Their number.
        """
        return sum(
            count for (topic, _v), count in self.counts.items() if topic is Topic.KIND
        )

    def rows(self) -> Iterator[tuple[str, str, int]]:
        """The lines of the sheet: topic, value, number of files.

        Yields:
            The lines, topic by topic, the most frequent value first.
        """
        labels = _topic_labels()
        for topic in Topic:
            found = [(value, n) for (t, value), n in self.counts.items() if t is topic]
            if topic in _IN_VALUE_ORDER:
                found.sort()
            else:
                found.sort(key=lambda item: (-item[1], item[0]))
            for value, count in found:
                yield labels[topic], value, count
        if self.groups:
            yield (
                labels[Topic.DUPLICATES],
                _("groups of identical files"),
                len(self.groups),
            )


def _topic_labels() -> dict[Topic, str]:
    """Name the topics in the active language.

    Returns:
        Topic → its label.
    """
    return {
        Topic.KIND: _("Kind"),
        Topic.YEAR: _("Year"),
        Topic.CAMERA: _("Camera"),
        Topic.FORMAT: _("Format"),
        Topic.INTEGRITY: _("Integrity"),
        Topic.DATE: _("Date taken"),
        Topic.PLACE: _("Place"),
        Topic.DUPLICATES: _("Duplicates"),
    }
