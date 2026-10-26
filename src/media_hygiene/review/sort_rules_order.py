"""*Your rules* shown by kind, then by period, the latest first (0395).

`config.toml` keeps its own order, which decides (the first sure rule wins); the dialog
only shows the rules otherwise: the kinds in a fixed order (dates, folder names, every
year…, the built-in rules last), each under a heading in the user's words, then by the
first day they cover — a `date_range` by its own, any other rule by the first day of the
event holding most of its files (0393) — the latest first; a rule that decided nothing
comes last in its kind.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.review.sort_rules_view import RuleLine

_RANGE: Final = ".."
_NO_DAY: Final = 1  # after every real day, negated
_KINDS: Final = (
    RuleMatch.DATE_RANGE,
    RuleMatch.PATH,
    RuleMatch.CALENDAR,
    RuleMatch.KIND,
    RuleMatch.CAMERA,
    RuleMatch.SUBJECT,
    RuleMatch.PERSON,
    RuleMatch.PLACE,
    RuleMatch.TRIP,
    RuleMatch.FOLDER_TOWN,
    RuleMatch.OTHER_CATEGORY,
)


def group_of(line: RuleLine) -> str:
    """The heading of a rule's kind, in the user's words.

    Args:
        line: The rule.

    Returns:
        E.g. `Dates`, `Folder names`; the built-in rules share one heading.
    """
    if line.built_in:
        return _("Built in: your own folders")
    names = {
        RuleMatch.DATE_RANGE: _("Dates"),
        RuleMatch.PATH: _("Folder and file names"),
        RuleMatch.CALENDAR: _("Days of every year"),
        RuleMatch.KIND: _("Kinds of files"),
        RuleMatch.CAMERA: _("Cameras"),
        RuleMatch.SUBJECT: _("What the photos show"),
        RuleMatch.PERSON: _("People"),
        RuleMatch.PLACE: _("Your places"),
        RuleMatch.TRIP: _("Trips"),
        RuleMatch.FOLDER_TOWN: _("Towns in folder names"),
        RuleMatch.OTHER_CATEGORY: _("Everything else"),
    }
    return names.get(RuleMatch(line.match), line.match)


def shown_order(lines: Sequence[RuleLine]) -> list[RuleLine]:
    """The rules as the dialog shows them: by kind, then the latest period first.

    Args:
        lines: The rules, in the file's order.

    Returns:
        The same rules, sorted; the file's order breaks the ties.
    """
    kinds = {kind.value: index for index, kind in enumerate(_KINDS)}

    def key(line: RuleLine) -> tuple[int, bool, int, int]:
        """Sort one rule.

        Args:
            line: The rule.

        Returns:
            Its kind, whether it decided nothing, its first day (negated: the latest
            first; none: last), its place in the file.
        """
        kind = len(_KINDS) if line.built_in else kinds.get(line.match, len(_KINDS))
        first = line.dates.split(_RANGE)[0] if line.dates else line.first
        day = -date.fromisoformat(first).toordinal() if first else _NO_DAY
        return (kind, line.files == 0 and not line.built_in, day, line.position)

    return sorted(lines, key=key)
