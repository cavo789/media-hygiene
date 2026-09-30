"""The test of each rule: does it match a file? Built once per run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.models import DateSource, SortReason
from media_hygiene.classify.rules.calendar import parse_one_off, parse_recurring
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.rules.matchers import KIND_TESTS, camera_test, path_test

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from media_hygiene.classify.models import Dating, Event, MediaInput
    from media_hygiene.classify.rules.calendar import OneOff, Recurring
    from media_hygiene.classify.rules.matchers import Test
    from media_hygiene.classify.signals import Signal
    from media_hygiene.config.classify_rules import ClassifyRule

_FOLDER_REASONS: Final = frozenset(
    {SortReason.EXISTING_FOLDER, SortReason.PERSON_FOLDER}
)


@dataclass(frozen=True, slots=True)
class RuleFacts:
    """What the rules read besides the file: dates, folders, events, host paths."""

    datings: Mapping[Path, Dating]
    folders: Mapping[Path, Signal]  # what the folders say, event neighbours joined
    event_of: Mapping[Path, Event]
    host: Callable[[Path], str]


def build_test(rule: ClassifyRule, facts: RuleFacts) -> Test:
    """Build the test of one rule.

    Args:
        rule: The rule, checked at load time.
        facts: The facts the date and path tests read.

    Returns:
        A test telling whether the rule matches a file.
    """
    folders = facts.folders
    builders: dict[RuleMatch, Callable[[], Test]] = {
        RuleMatch.EXISTING_FOLDER: lambda: (
            lambda file: folders[file.path].reason in _FOLDER_REASONS
        ),
        RuleMatch.EVENT_NEIGHBOUR: lambda: (
            lambda file: folders[file.path].reason is SortReason.EVENT_NEIGHBOUR
        ),
        RuleMatch.CALENDAR: lambda: _dated(parse_recurring(rule.dates), facts),
        RuleMatch.DATE_RANGE: lambda: _dated(parse_one_off(rule.dates), facts),
        RuleMatch.KIND: lambda: KIND_TESTS[rule.kind] if rule.kind else _never,
        RuleMatch.PATH: lambda: path_test(rule.pattern, facts.host),
        RuleMatch.CAMERA: lambda: camera_test(rule.pattern),
        RuleMatch.OTHER_CATEGORY: lambda: _always,
    }
    return builders[rule.match]()


def _dated(window: Recurring | OneOff, facts: RuleFacts) -> Test:
    """A test of dates: the event when the file has one, else its own reliable date.

    Args:
        window: The days of the rule.
        facts: Dates and events.

    Returns:
        The test.
    """
    events = {event.event_id: event for event in facts.event_of.values()}
    taken = frozenset(
        event_id
        for event_id, event in events.items()
        if 2 * sum(window.contains(facts.datings[p].when.date()) for p in event.paths)
        >= len(event.paths)
    )

    def test(file: MediaInput) -> bool:
        """Tell whether one file falls in the window.

        Args:
            file: The file.

        Returns:
            True for a file of a matching event, or a lone file dated in it.
        """
        event = facts.event_of.get(file.path)
        if event is not None:
            return event.event_id in taken
        dating = facts.datings[file.path]
        return dating.source is not DateSource.MTIME and window.contains(
            dating.when.date()
        )

    return test


def _always(_file: MediaInput) -> bool:
    """Match every file: the fallback.

    Returns:
        True.
    """
    return True


def _never(_file: MediaInput) -> bool:
    """Match no file.

    Returns:
        False.
    """
    return False
