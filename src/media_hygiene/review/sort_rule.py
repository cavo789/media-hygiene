"""*Remember as a rule* (0392): the event shown written down as a `date_range` rule.

The page sends the rule as the user validated it in its dialog; `preview` tells what it
would take on the plan the page shows, as `classify` reads a date rule (an event goes to
it when at least half of its photos fall on its days; a file of no event by its own
date): the files of this event, those of other folders on the same days, the rules it
overlaps. Saving writes it into `config.toml` (`classify.rules_file`) and records the
event's choice: *Sort this event now* works at once, the rule serves the next runs.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.rules.calendar import parse_one_off
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow
    from media_hygiene.classify.rules.calendar import OneOff

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_SHOWN_FOLDERS: Final = 3


class RuleIn(BaseModel):
    """`POST /api/rule/preview` and `/api/rule`: the rule of an event, as validated."""

    model_config = _FROZEN

    event: str
    name: str
    first: str  # ISO day
    last: str
    category: str
    keep_folders: bool = True
    replaces: str = (
        ""  # *Turn into dates* (0393): the folder-name rule replaced in place
    )

    def rule(self) -> ClassifyRule:
        """The rule, checked as `config.toml` is.

        Returns:
            It.
        """
        return ClassifyRule(
            name=self.name.strip(),
            match=RuleMatch.DATE_RANGE,
            dates=f"{self.first}..{self.last}",
            category=self.category.strip().strip("/"),
            keep_folders=self.keep_folders,
        )


class RulePreview(BaseModel):
    """What a rule would take on the plan shown."""

    model_config = _FROZEN

    files: int  # every file it would take
    this_event: int  # of which files of the event shown
    others: int  # files of other events, or of no event, on the same days
    folders: tuple[str, ...]  # where those others are: `Photos Chloé (230)`
    overlaps: tuple[str, ...]  # the `date_range` rules sharing a day with it
    taken: bool  # another rule has the same name
    lost: int = 0  # files the rule replaced decided, which this one does not take


def preview(
    plan: ClassifyPlan,
    asked: RuleIn,
    written: Sequence[ClassifyRule],
) -> RulePreview:
    """Count what a rule would take, as `classify` reads a date rule.

    Args:
        plan: The plan the page shows.
        asked: The rule asked for, its event, the rule it replaces if any.
        written: The rules of `config.toml`.

    Returns:
        The counts.
    """
    rule, event_id, replaces = asked.rule(), asked.event, asked.replaces
    window = parse_one_off(rule.dates)
    events = _events_taken(plan.rows, window)
    taken = [row for row in plan.rows if _takes(row, events, window)]
    kept = {row.id for row in taken}
    mine = sum(1 for row in taken if row.event_id == event_id)
    others = [row for row in taken if row.event_id != event_id]
    folders = Counter(_last(row.parent) for row in others).most_common(_SHOWN_FOLDERS)
    return RulePreview(
        files=len(taken),
        this_event=mine,
        others=len(others),
        folders=tuple(f"{name} ({count})" for name, count in folders),
        overlaps=tuple(overlapping(window, written)),
        taken=any(
            other.name.casefold() == rule.name.casefold()
            for other in written
            if other.name != replaces
        ),
        lost=sum(1 for row in plan.rows if row.rule == replaces and row.id not in kept)
        if replaces
        else 0,
    )


def _events_taken(rows: Sequence[PlanRow], window: OneOff) -> frozenset[str]:
    """The events at least half of whose dated files fall on the rule's days.

    Args:
        rows: The plan's rows.
        window: The rule's days.

    Returns:
        Their ids.
    """
    inside: Counter[str] = Counter()
    dated: Counter[str] = Counter()
    for row in rows:
        if row.event_id and row.date:
            dated[row.event_id] += 1
            inside[row.event_id] += _in(row, window)
    return frozenset(
        event for event, count in dated.items() if 2 * inside[event] >= count
    )


def _takes(row: PlanRow, events: frozenset[str], window: OneOff) -> bool:
    """Tell whether a rule takes one file: its event's, else its own date.

    Args:
        row: The file.
        events: The events the rule takes.
        window: The rule's days.

    Returns:
        True when it does.
    """
    if row.values is None:
        return False  # left as it is: no rule moves it
    return row.event_id in events if row.event_id else _in(row, window)


def _in(row: PlanRow, window: OneOff) -> bool:
    """Tell whether a file was taken on the rule's days.

    Args:
        row: The file.
        window: The days.

    Returns:
        True for a dated file of those days.
    """
    return row.date is not None and window.contains(date.fromisoformat(row.date[:10]))


def overlapping(window: OneOff, rules: Iterable[ClassifyRule]) -> list[str]:
    """The `date_range` rules sharing a day with a window: the first listed wins there.

    Args:
        window: The new rule's days.
        rules: The rules of `config.toml`.

    Returns:
        Their names and days.
    """
    return [
        f"{rule.name} ({rule.dates})"
        for rule in rules
        if rule.match is RuleMatch.DATE_RANGE
        and window.overlaps(parse_one_off(rule.dates))
    ]


def _last(folder: str) -> str:
    r"""The last name of a host folder.

    Args:
        folder: `C:\Photos\2019\Photos Chloé`.

    Returns:
        `Photos Chloé`.
    """
    return folder.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
