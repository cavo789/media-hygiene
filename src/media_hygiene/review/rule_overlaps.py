"""The `date_range` rules a new one shares days with: the first listed wins there.

Events whose cameras differ share their days without a clash (0556): a file goes to
the event of its camera, so they are not listed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.rules.calendar import cameras_apart, parse_one_off
from media_hygiene.classify.rules.kinds import RuleMatch

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.classify.rules.calendar import OneOff
    from media_hygiene.config.classify_rules import ClassifyRule


def overlapping(
    window: OneOff, rules: Iterable[ClassifyRule], devices: tuple[str, ...] = ()
) -> list[str]:
    """The `date_range` rules sharing a day with a window, its cameras apart.

    Args:
        window: The new rule's days.
        rules: The rules of `config.toml`.
        devices: The new rule's cameras; none: every rule of its days clashes.

    Returns:
        Their names and days.
    """
    return [
        f"{rule.name} ({rule.dates})"
        for rule in rules
        if rule.match is RuleMatch.DATE_RANGE
        and window.overlaps(parse_one_off(rule.dates))
        and not cameras_apart(devices, rule.devices)
    ]
