"""Events: files taken close together, across folders, cut in two levels.

A session ends after `session_gap_hours` without a shot; sessions closer than
`merge_gap_hours` make one event, so that a night does not cut an outing in two. Groups
smaller than `min_event_size` are not events: their files fall back to their month.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.models import DateSource, Event

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.classify.models import Dating
    from media_hygiene.config.classify_settings import ClassifySettings

_ID_LENGTH: Final = 12


@dataclass(frozen=True, slots=True)
class EventRules:
    """The gaps and the minimum size, from `[classify]`."""

    session_gap: timedelta
    merge_gap: timedelta
    min_size: int

    @classmethod
    def of(cls, session_hours: float, merge_hours: float, min_size: int) -> EventRules:
        """Build the rules from hours.

        Args:
            session_hours: Gap ending a session.
            merge_hours: Largest gap between sessions of one event.
            min_size: Fewer files are not an event.

        Returns:
            The rules.
        """
        return cls(
            timedelta(hours=session_hours), timedelta(hours=merge_hours), min_size
        )


def find_events(
    dated: Sequence[tuple[Path, datetime]],
    rules: EventRules,
    labels: Mapping[Path, str],
) -> tuple[Event, ...]:
    """Group files into events.

    Args:
        dated: Files with a trusted date.
        rules: Gaps and minimum size.
        labels: The meaningful folder label of each file, when it has one.

    Returns:
        The events, oldest first.
    """
    ordered = sorted(dated, key=lambda item: (item[1], str(item[0])))
    # Without positions, sessions closer than the merge gap are one event: the two
    # levels meet in one gap. Sessions matter alone for sampling and trips.
    gap = max(rules.session_gap, rules.merge_gap)
    groups: list[list[tuple[Path, datetime]]] = []
    for item in ordered:
        if groups and item[1] - groups[-1][-1][1] <= gap:
            groups[-1].append(item)
        else:
            groups.append([item])
    return tuple(
        _event(group, labels) for group in groups if len(group) >= rules.min_size
    )


def _event(group: list[tuple[Path, datetime]], labels: Mapping[Path, str]) -> Event:
    """Describe one group of files as an event.

    Args:
        group: Its files and dates, in date order.
        labels: Meaningful folder labels.

    Returns:
        The event, with a stable id and its dominant label.
    """
    first_path, start = group[0]
    seed = f"{first_path}|{start.isoformat()}".encode()
    found = Counter(labels[path] for path, _when in group if path in labels)
    label = found.most_common(1)[0][0] if found else ""
    return Event(
        event_id=hashlib.sha256(seed).hexdigest()[:_ID_LENGTH],
        start=start,
        end=group[-1][1],
        paths=tuple(path for path, _when in group),
        label=label,
    )


def trusted_events(
    datings: Mapping[Path, Dating],
    labels: Mapping[Path, str],
    settings: ClassifySettings,
) -> tuple[Event, ...]:
    """Group the files with a trusted date into events.

    Args:
        datings: The date of each file.
        labels: The meaningful folder label of each file, when it has one.
        settings: `[classify]`: the gaps and the minimum size.

    Returns:
        The events.
    """
    trusted = [
        (path, dating.when)
        for path, dating in datings.items()
        if dating.source is not DateSource.MTIME
    ]
    rules = EventRules.of(
        settings.session_gap_hours, settings.merge_gap_hours, settings.min_event_size
    )
    return find_events(trusted, rules, labels)
