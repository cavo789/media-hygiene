"""`[[classify.rules]]` — what the user knows, written once: dates, paths, cameras.

Each rule has a `name`, shown as the reason of the files it decides. The rules are read
in order: the first whose score reaches `sure` wins. A rule refused at load time names
itself. The default list is an example, written in the generated `config.toml`.
"""

from __future__ import annotations

import re
from itertools import combinations
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from media_hygiene.classify.layout import check_layout
from media_hygiene.classify.rules.calendar import parse_one_off, parse_recurring
from media_hygiene.classify.rules.kinds import BUILT_IN, FileKind, RuleMatch

if TYPE_CHECKING:
    from collections.abc import Sequence

_NEEDS = {
    RuleMatch.CALENDAR: "dates",
    RuleMatch.DATE_RANGE: "dates",
    RuleMatch.KIND: "kind",
    RuleMatch.PATH: "pattern",
    RuleMatch.CAMERA: "pattern",
    RuleMatch.SUBJECT: "categories",
    RuleMatch.OTHER_CATEGORY: "category",
}
_OPTIONAL = ("dates", "kind", "pattern", "categories", "per_photo")


class ClassifyRule(BaseModel):
    """One rule: what it matches, the category it gives, and how sure it is.

    No category: the files it matches stay where they are.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    match: RuleMatch
    category: str = ""
    dates: str = ""  # `calendar`: `12-24..12-26`; `date_range`: `2023-07-01..07-15`
    pattern: str = ""  # `path`, `camera`: a regular expression, searched
    kind: FileKind | None = None
    categories: tuple[str, ...] = ()  # `subject`: what the model chooses from
    per_photo: bool = False  # `subject`: describe every photo, not samples
    score: int | None = Field(default=None, ge=0, le=100)  # None: `[classify] scores`

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        """Refuse a rule that cannot work, naming it.

        Returns:
            The rule, unchanged.

        Raises:
            ValueError: A field is missing, useless or invalid.
        """
        try:
            _check(self)
        except (ValueError, re.error) as exc:
            message = f"rule {self.name!r}: {exc}"
            raise ValueError(message) from exc
        return self


def _check(rule: ClassifyRule) -> None:
    """Check the fields of one rule against its `match`.

    Args:
        rule: The rule.

    Raises:
        ValueError: A needed field is empty, another one is set, or a value is invalid.
    """
    needed = _NEEDS.get(rule.match)
    if needed and not getattr(rule, needed):
        message = f"match = {rule.match.value!r} needs {needed}"
        raise ValueError(message)
    for field in (*_OPTIONAL, "category"):
        if field != needed and getattr(rule, field) and not _uses(rule.match, field):
            message = f"{field} is not used by match = {rule.match.value!r}"
            raise ValueError(message)
    if rule.match is RuleMatch.CALENDAR:
        parse_recurring(rule.dates)
    if rule.match is RuleMatch.DATE_RANGE:
        parse_one_off(rule.dates)
    if rule.pattern:
        re.compile(rule.pattern)
    if "{category}" in rule.category:
        message = "{category} cannot be used in a category"
        raise ValueError(message)
    check_layout(rule.category)
    _check_categories(rule.categories)


def _check_categories(categories: tuple[str, ...]) -> None:
    """Check the categories a `subject` rule offers the model.

    Args:
        categories: The rule's `categories`.

    Raises:
        ValueError: One is empty, holds a placeholder, or is no folder name.
    """
    for category in categories:
        if not category.strip() or "{" in category:
            message = f"{category!r} is not a category: no placeholder, not empty"
            raise ValueError(message)
        check_layout(category)


def _uses(match: RuleMatch, field: str) -> bool:
    """Tell whether a kind of rule reads a field.

    Args:
        match: The kind of rule.
        field: `category`, or an optional field.

    Returns:
        True when it does.
    """
    if field == "category":
        return match not in BUILT_IN and match is not RuleMatch.SUBJECT
    if field == "per_photo":
        return match is RuleMatch.SUBJECT
    return _NEEDS.get(match) == field


def unique_names(rules: tuple[ClassifyRule, ...]) -> tuple[ClassifyRule, ...]:
    """Refuse two rules with the same name: the name tells them apart.

    Args:
        rules: The rules.

    Returns:
        Them, unchanged.

    Raises:
        ValueError: A name is used twice.
    """
    seen: set[str] = set()
    for rule in rules:
        if rule.name.casefold() in seen:
            message = f"two rules are named {rule.name!r}"
            raise ValueError(message)
        seen.add(rule.name.casefold())
    return rules


def overlapping_ranges(rules: Sequence[ClassifyRule]) -> tuple[tuple[str, str], ...]:
    """The pairs of date ranges sharing a day: the first one listed wins.

    Args:
        rules: The rules.

    Returns:
        The names of each such pair, in list order.
    """
    ranges = [
        (rule.name, parse_one_off(rule.dates))
        for rule in rules
        if rule.match is RuleMatch.DATE_RANGE
    ]
    return tuple(
        (first, second)
        for (first, one), (second, other) in combinations(ranges, 2)
        if one.overlaps(other)
    )


DEFAULT_RULES = (
    ClassifyRule(name="Films and series", match=RuleMatch.KIND, kind=FileKind.DOWNLOAD),
    ClassifyRule(name="Existing folders", match=RuleMatch.EXISTING_FOLDER),
    ClassifyRule(
        name="Screenshots and documents",
        match=RuleMatch.KIND,
        kind=FileKind.SCREENSHOT,
        category="Documents and screenshots",
    ),
    ClassifyRule(name="Event neighbours", match=RuleMatch.EVENT_NEIGHBOUR),
    ClassifyRule(
        name="Christmas",
        match=RuleMatch.CALENDAR,
        dates="12-24..12-26",
        category="Parties/Christmas",
    ),
    ClassifyRule(
        name="New Year",
        match=RuleMatch.CALENDAR,
        dates="12-31..01-01",
        category="Parties/New Year",
    ),
)
