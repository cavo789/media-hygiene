"""The rule of a period (0396): the rule typed, its trial, the date rules of a file."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.rules.calendar import parse_one_off
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.review.serving import json_response

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from pathlib import Path

    from pydantic import ValidationError

    from media_hygiene.classify.rules.calendar import OneOff
    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.review.http import Response
    from media_hygiene.search.models import Hit

SEPARATOR: Final = "/"
WINDOWS: Final = "\\"


@dataclass(frozen=True, slots=True)
class RuleTry:
    """A rule to try, the name of the rule it replaces (or empty), the files to try."""

    rule: ClassifyRule
    replaces: str
    files: Sequence[PhotoVersion]


@dataclass(frozen=True, slots=True)
class Tried:
    """Where `sort` would put one file with the rule saved, and which rule decides."""

    folder: str | None  # below the target root, `/`-separated; None: it stays
    rule: str  # the rule that decides; empty: none
    taken: bool  # the rule tried decides
    # Its event: first and last day (ISO), files; None: a file of no event.
    event: tuple[str, str, int] | None = None


type Trial = Callable[[RuleTry], Mapping[Path, Tried]]
# Sorts a group: container path → its folder below its root, the rule's category;
# answers the run read back (0397).
type Sorter = Callable[[Mapping[Path, str], str], Mapping[str, object]]


class PeriodRuleIn(BaseModel):
    """The rule typed in the dialog: its days, name, folder, the rule it replaces."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    first: date
    last: date
    category: str
    keep_folders: bool = True
    replaces: str = ""  # *Update a rule…*: the name of the rule replaced in place

    def rule(self) -> ClassifyRule:
        """The rule, checked as `config.toml` is.

        Returns:
            It; days in the wrong order are put back in order.
        """
        first, last = sorted((self.first, self.last))
        return ClassifyRule(
            name=self.name.strip(),
            match=RuleMatch.DATE_RANGE,
            dates=f"{first.isoformat()}..{last.isoformat()}",
            category=self.category.strip().strip(SEPARATOR),
            keep_folders=self.keep_folders,
        )


def dated_rules(rules: Sequence[ClassifyRule]) -> list[dict[str, object]]:
    """The `date_range` rules, the latest first (by their first day, 0395).

    Args:
        rules: The rules of `config.toml`.

    Returns:
        Each one's name, days, folder and `keep_folders`.
    """
    dated = [rule for rule in rules if rule.match is RuleMatch.DATE_RANGE]
    dated.sort(key=lambda rule: parse_one_off(rule.dates).start, reverse=True)
    return [line(rule) for rule in dated]


def line(rule: ClassifyRule) -> dict[str, object]:
    """One date rule for the page.

    Args:
        rule: The rule.

    Returns:
        Its name, days (`first`, `last`, `dates`), folder and `keep_folders`.
    """
    window = parse_one_off(rule.dates)
    return {
        "name": rule.name,
        "dates": rule.dates,
        "first": window.start.isoformat(),
        "last": window.end.isoformat(),
        "category": rule.category,
        "keep_folders": rule.keep_folders,
    }


def shown_in(hit: Hit, tried: Mapping[Path, Tried], window: OneOff) -> bool:
    """Tell whether a file is shown: the rule takes it, or it is of its days.

    Args:
        hit: The file.
        tried: Where each file would go.
        window: The rule's days.

    Returns:
        True when it is.
    """
    where = tried.get(hit.photo.path)
    if where is not None and where.taken:
        return True
    return hit.date is not None and window.contains(date.fromisoformat(hit.date))


def where_of(tried: Tried | None) -> dict[str, object]:
    """Where one file would go, for its card.

    Args:
        tried: What the trial said of it; None: not classified (not a media file).

    Returns:
        `to` (the folder, as Windows writes it; empty: it stays), `by` (the rule that
        decides), `taken`.
    """
    if tried is None:
        return {"to": "", "by": "", "taken": False}
    folder = (tried.folder or "").replace(SEPARATOR, WINDOWS)
    return {"to": folder, "by": tried.rule, "taken": tried.taken}


def wider(
    hits: Sequence[Hit], tried: Mapping[Path, Tried], window: OneOff
) -> list[dict[str, object]]:
    """The events the rule leaves because most of their files fall outside its days.

    A date rule takes an event when at least half of its files fall on its days: an
    evening shot on two days, typed as one, is left whole. The page then offers to
    widen the period to the event's days.

    Args:
        hits: The files shown.
        tried: Where each file would go, and its event.
        window: The rule's days.

    Returns:
        Each such event's first and last day, its files, and how many of them are on
        the rule's days.
    """
    events: dict[tuple[str, str, int], int] = {}
    for hit in hits:
        where = tried.get(hit.photo.path)
        if where is None or where.taken or where.event is None:
            continue
        first, last, _files = where.event
        inside = window.contains(date.fromisoformat(first)) and window.contains(
            date.fromisoformat(last)
        )
        if not inside:
            events[where.event] = events.get(where.event, 0) + 1
    return [
        {"first": first, "last": last, "files": files, "here": here}
        for (first, last, files), here in events.items()
    ]


def refused_rule(error: ValidationError) -> Response:
    """Answer that the rule typed cannot be written, and why.

    Args:
        error: What pydantic said.

    Returns:
        400, with the first message.
    """
    said = error.errors()[0]["msg"] if error.errors() else str(error)
    return json_response(HTTPStatus.BAD_REQUEST, {"error": said})
