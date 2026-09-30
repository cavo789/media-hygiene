"""Give each edited event of the previous plan its new event(s).

An event goes to the new event that holds most of its files. When it was split, every
part made of its files for at least half gets the edit too. When two named events
merged, the one that brought the most files wins; the other one is listed.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from media_hygiene.classify.plan_file import ClassifyPlan


@dataclass(frozen=True, slots=True)
class EventMatch:
    """The rows of both plans the matching reads."""

    old: ClassifyPlan | None
    new: ClassifyPlan
    rows: Mapping[str, str]  # previous row id → new row id
    applied: frozenset[str]  # previous rows a sort already moved


type Targets = dict[str, tuple[str, ...] | None]


@dataclass(frozen=True, slots=True)
class _Lookup:
    """Both plans indexed once: 70,000 rows are not read again for every event."""

    old_events: Mapping[str, tuple[str, ...]] | None  # None: the previous plan is lost
    new_event: Mapping[str, str]  # new row id → its event id
    sizes: Mapping[str, int]  # new event id → its files

    @classmethod
    def of(cls, match: EventMatch) -> _Lookup:
        """Index the plans.

        Args:
            match: Both plans.

        Returns:
            The lookups.
        """
        old = match.old
        return cls(
            {event.id: event.rows for event in old.events} if old else None,
            {row.id: row.event_id for row in match.new.rows},
            {event.id: len(event.rows) for event in match.new.events},
        )


def event_targets(
    keys: Iterable[str], match: EventMatch
) -> tuple[Targets, frozenset[str]]:
    """The new events of each previous event.

    Args:
        keys: The previous events that hold an edit.
        match: Both plans and the rows matched.

    Returns:
        Previous event id → its new event ids (empty: gone or merged), or None when
        a sort already applied it to every one of its files; and the previous events
        that lost every new event to another one (merged).
    """
    lookup = _Lookup.of(match)
    shares: dict[str, Counter[str]] = {}
    targets: Targets = {}
    for key in keys:
        found = _shares(key, match, lookup)
        if found is None:
            targets[key] = None
            continue
        shares[key] = found
        targets[key] = _chosen(found, lookup.sizes)
    settled = _settle(targets, shares)
    merged = frozenset(
        key for key, chosen in targets.items() if chosen and not settled[key]
    )
    return settled, merged


def _shares(key: str, match: EventMatch, lookup: _Lookup) -> Counter[str] | None:
    """How many files of a previous event each new event holds.

    Args:
        key: A previous event id.
        match: Both plans and the rows matched.
        lookup: The plans, indexed.

    Returns:
        New event id → files; None when every file of the event was sorted.
    """
    old = lookup.old_events
    old_rows = old.get(key) if old is not None else None
    if old_rows is None:  # the previous plan or event is lost: event ids are stable
        return Counter({key: 1}) if key in lookup.sizes else Counter()
    left = [row for row in old_rows if row not in match.applied]
    if old_rows and not left:
        return None
    new_event = lookup.new_event
    return Counter(
        new_event[new_id]
        for row in left
        if (new_id := match.rows.get(row)) and new_event.get(new_id)
    )


def _chosen(found: Counter[str], sizes: Mapping[str, int]) -> tuple[str, ...]:
    """The new event holding most of the files, and every part mostly made of them.

    Args:
        found: New event id → files of the previous event it holds.
        sizes: New event id → its files.

    Returns:
        The new event ids, the main one first.
    """
    if not found:
        return ()
    main = found.most_common(1)[0][0]
    parts = [
        event_id
        for event_id, count in found.most_common()
        if event_id != main and 2 * count >= sizes.get(event_id, 0)
    ]
    return (main, *parts)


def _settle(targets: Targets, shares: Mapping[str, Counter[str]]) -> Targets:
    """Give a new event claimed by several previous ones to the largest share.

    Args:
        targets: Previous event → new events.
        shares: Previous event → files per new event.

    Returns:
        The targets, each new event kept by one previous event only.
    """
    claims: defaultdict[str, list[str]] = defaultdict(list)
    for key, chosen in targets.items():
        for event_id in chosen or ():
            claims[event_id].append(key)
    winner = {
        event_id: max((shares[k][event_id], k) for k in keys)[1]
        for event_id, keys in claims.items()
    }
    return {
        key: None
        if chosen is None
        else tuple(event_id for event_id in chosen if winner[event_id] == key)
        for key, chosen in targets.items()
    }
