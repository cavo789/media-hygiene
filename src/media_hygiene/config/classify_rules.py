"""`[[classify.rules]]` — what the user knows, written once: dates, paths, people.

Each rule has a `name`, shown as the reason of the files it decides. The rules are read
in order: the first whose score reaches `sure` wins. A rule refused at load time names
itself. The default list is an example, written in the generated `config.toml`.
"""

from __future__ import annotations

import re
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from media_hygiene.classify.layout import check_layout
from media_hygiene.classify.rules.calendar import parse_one_off, parse_recurring
from media_hygiene.classify.rules.kinds import BUILT_IN, FileKind, RuleMatch
from media_hygiene.config.rule_checks import check_categories, check_category
from media_hygiene.i18n import _

_NEEDS = {
    RuleMatch.CALENDAR: "dates",
    RuleMatch.DATE_RANGE: "dates",
    RuleMatch.KIND: "kind",
    RuleMatch.PATH: "pattern",
    RuleMatch.CAMERA: "pattern",
    RuleMatch.SUBJECT: "categories",
    RuleMatch.PERSON: "names",
    RuleMatch.OTHER_CATEGORY: "category",
}
# The fields only one kind of rule reads, besides the one it needs.
_ONLY = {
    "per_photo": RuleMatch.SUBJECT,
    "all": RuleMatch.PERSON,
    "min_share": RuleMatch.PERSON,
}
_OPTIONAL = ("dates", "kind", "pattern", "categories", "names", *_ONLY)


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
    names: tuple[str, ...] = ()  # `person`: names of `[[people.person]]`, any of them
    all: bool = False  # `person`: every name, not any of them
    # `person`: the percentage of an event's photos the people must be on; None: 10.
    min_share: int | None = Field(default=None, ge=1, le=100)
    score: int | None = Field(default=None, ge=0, le=100)  # None: `[classify] scores`
    keep_folders: bool = False  # the folders the user named stay below the category
    # Its own layout, not `[classify] layout` (0402): screenshots out of the years.
    layout: str = ""

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
            message = _("rule '{name}': {reason}").format(name=self.name, reason=exc)
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
        message = _("match = '{match}' needs {field}")
        message = message.format(match=rule.match.value, field=needed)
        raise ValueError(message)
    for field in (*_OPTIONAL, "category"):
        if field != needed and getattr(rule, field) and not _uses(rule.match, field):
            message = _("{field} is not used by match = '{match}'")
            message = message.format(field=field, match=rule.match.value)
            raise ValueError(message)
    if rule.match is RuleMatch.CALENDAR:
        parse_recurring(rule.dates)
    if rule.match is RuleMatch.DATE_RANGE:
        parse_one_off(rule.dates)
    if rule.pattern:
        re.compile(rule.pattern)
    check_category(rule)
    check_categories(rule.categories, rule.names)
    if rule.layout:
        check_layout(rule.layout)


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
    if field in _ONLY:
        return match is _ONLY[field]
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
            message = _("two rules are named '{name}'").format(name=rule.name)
            raise ValueError(message)
        seen.add(rule.name.casefold())
    return rules


DEFAULT_RULES = (
    ClassifyRule(name="Films and series", match=RuleMatch.KIND, kind=FileKind.DOWNLOAD),
    ClassifyRule(name="Existing folders", match=RuleMatch.EXISTING_FOLDER),
    # No category: screenshots stay where they are, out of the years (0402).
    ClassifyRule(
        name="Screenshots and documents", match=RuleMatch.KIND, kind=FileKind.SCREENSHOT
    ),
    ClassifyRule(name="Event neighbours", match=RuleMatch.EVENT_NEIGHBOUR),
    ClassifyRule(name="Same moment", match=RuleMatch.SAME_MOMENT),
    ClassifyRule(
        name="Christmas",
        match=RuleMatch.CALENDAR,
        dates="12-24..12-26",
        category="Christmas",
    ),
    ClassifyRule(
        name="New Year",
        match=RuleMatch.CALENDAR,
        dates="12-31..01-01",
        category="New Year",
    ),
)
