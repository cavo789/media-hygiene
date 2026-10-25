"""*Your rules* (0393): what each rule of `config.toml` decided on the plan shown.

A rule that decided nothing is dead: the page offers to remove it, one or all of them.
A folder-name rule (`match = "path"`) serves once, until `sort` moved its files out of
the folder it names; the page offers to turn it into a date rule, one by one, with the
days of the event holding most of its files (never its extreme dates: a pattern catches
badly dated photos too, measured on the maintainer's plan, 2026-10-25).
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.rules.kinds import BUILT_IN, RuleMatch

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.config.classify_rules import ClassifyRule

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class RuleLine(BaseModel):
    """One rule of `config.toml`, and what it decided."""

    model_config = _FROZEN

    name: str
    match: str
    category: str
    dates: str  # its own, for a date rule
    files: int  # decided by it at the run shown
    built_in: bool  # its category comes from the folders: never dead, never converted
    event: str  # the event holding most of its files; empty: none
    first: str  # that event's first and last day, for *Turn into dates*
    last: str


class RulesView(BaseModel):
    """`GET /api/rules`: every rule, in order, and the run they were seen on."""

    model_config = _FROZEN

    run: str  # the classify run the page shows: `20261013-191349-classify`
    rules: tuple[RuleLine, ...]


def rules_view(
    plan: ClassifyPlan, rules: Sequence[ClassifyRule], run: str
) -> RulesView:
    """Describe what each rule decided on a plan.

    Args:
        plan: The plan the page shows.
        rules: The rules of `config.toml`, in order.
        run: The classify run's folder name.

    Returns:
        The view.
    """
    decided = Counter(row.rule for row in plan.rows if row.rule)
    by_event: dict[str, Counter[str]] = {}
    for row in plan.rows:
        if row.rule and row.event_id:
            by_event.setdefault(row.rule, Counter())[row.event_id] += 1
    days = {event.id: (event.start[:10], event.end[:10]) for event in plan.events}
    lines = []
    for rule in rules:
        held = by_event.get(rule.name, Counter()).most_common(1)
        event = held[0][0] if held else ""
        first, last = days.get(event, ("", ""))
        lines.append(
            RuleLine(
                name=rule.name,
                match=rule.match.value,
                category=rule.category,
                dates=rule.dates if rule.match is RuleMatch.DATE_RANGE else "",
                files=decided.get(rule.name, 0),
                built_in=rule.match in BUILT_IN,
                event=event,
                first=first,
                last=last,
            )
        )
    return RulesView(run=run, rules=tuple(lines))
