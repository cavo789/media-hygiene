"""Which event a move joins (0556): an event is its name *and* its period.

`Turin` every two or three years is one folder each time: a move to `Turin` joins the
`Turin` whose period touches the photos' days (a day apart at most), else starts
another one. The rules of `config.toml` keep unique names: the first `Turin` is named
`Turin`, the next ones `Turin (April 2022)`; the page shows every event of a shared
name with its month, `Turin (July 2019)`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.layout import month_name
from media_hygiene.classify.rules.calendar import parse_one_off
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import date

NEAR: Final = timedelta(days=1)  # a photo of the day after still joins the event


@dataclass(frozen=True, slots=True)
class Moved:
    """What a move brings to an event: its folder name, days and cameras."""

    name: str  # the event's folder name: the rule's category
    days: tuple[date, ...]
    devices: tuple[str, ...] = ()


def events_named(rules: Sequence[ClassifyRule], name: str) -> list[ClassifyRule]:
    """The events of a name, in the file's order.

    Args:
        rules: The rules of `config.toml`.
        name: The event's folder name.

    Returns:
        The `date_range` rules of that category.
    """
    return [
        rule
        for rule in rules
        if rule.match is RuleMatch.DATE_RANGE
        and rule.category.casefold() == name.casefold()
    ]


def joined_event(events: Sequence[ClassifyRule], moved: Moved) -> ClassifyRule | None:
    """The event of that name whose period touches the days moved.

    Args:
        events: The events of the name.
        moved: The move.

    Returns:
        It; None: the move starts another event.
    """
    start, end = min(moved.days), max(moved.days)
    for rule in events:
        period = parse_one_off(rule.dates)
        if start <= period.end + NEAR and end >= period.start - NEAR:
            return rule
    return None


def label(rule: ClassifyRule, rules: Sequence[ClassifyRule]) -> str:
    """How the page names an event: with its month when another one has its name.

    Args:
        rule: The event.
        rules: The rules of `config.toml`.

    Returns:
        `Turin`, or `Turin (July 2019)`.
    """
    if len(events_named(rules, rule.category)) < 2:  # noqa: PLR2004 - "another one"
        return rule.category
    return with_month(rule)


def with_month(rule: ClassifyRule) -> str:
    """An event named with the month it starts: `Turin (July 2019)`.

    Args:
        rule: The event.

    Returns:
        Its name and month.
    """
    return f"{rule.category} ({_month_of(parse_one_off(rule.dates).start)})"


def new_event(events: Sequence[ClassifyRule], moved: Moved) -> ClassifyRule:
    """A new event of the move: `Turin`, or `Turin (April 2022)` beside another one.

    Args:
        events: The events of the name already written.
        moved: The move.

    Returns:
        The rule, its name unique among them.
    """
    start, end = min(moved.days), max(moved.days)
    rule_name = moved.name
    if events:
        rule_name = f"{moved.name} ({_month_of(start)})"
        if any(rule.name.casefold() == rule_name.casefold() for rule in events):
            rule_name = f"{moved.name} ({start.isoformat()})"
    return ClassifyRule(
        name=rule_name,
        match=RuleMatch.DATE_RANGE,
        category=moved.name,
        dates=f"{start.isoformat()}..{end.isoformat()}",
        devices=moved.devices,
    )


def widened(rule: ClassifyRule, moved: Moved) -> ClassifyRule:
    """The event widened to the days moved, their cameras added.

    Args:
        rule: The event joined.
        moved: The move.

    Returns:
        The new rule, same name.
    """
    held = parse_one_off(rule.dates)
    start, end = min(held.start, *moved.days), max(held.end, *moved.days)
    return rule.model_copy(
        update={
            "dates": f"{start.isoformat()}..{end.isoformat()}",
            "devices": tuple(sorted({*rule.devices, *moved.devices})),
        }
    )


def _month_of(day: date) -> str:
    """`July 2019`, translated.

    Args:
        day: A day.

    Returns:
        Its month and year.
    """
    return f"{month_name(day.month)} {day.year}"
