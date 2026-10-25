"""The checks of the categories a `[[classify.rules]]` rule gives, at load time."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.ai.categories import names as names_of
from media_hygiene.classify.layout import check_layout
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.config.classify_rules import ClassifyRule


def check_category(rule: ClassifyRule) -> None:
    """Check the category a rule gives, and what keeps folders below it.

    Args:
        rule: The rule.

    Raises:
        ValueError: `keep_folders` without a category, or a category that is no
            folder name.
    """
    if rule.keep_folders and not rule.category:
        raise ValueError(_("keep_folders needs a category to keep the folders below"))
    if "{category}" in rule.category:
        raise ValueError(_("{category} cannot be used in a category"))
    check_layout(rule.category)


def check_categories(categories: tuple[str, ...], names: tuple[str, ...]) -> None:
    """Check the categories a `subject` rule offers the model, the names of a `person`.

    Args:
        categories: The rule's `categories`.
        names: The rule's `names`.

    Raises:
        ValueError: One is empty, holds a placeholder, or is no folder name.
    """
    if any(not name.strip() for name in names):
        raise ValueError(_("a name in names is empty"))
    for category in names_of(categories):  # `Name = definition`: the name is the folder
        if not category or "{" in category:
            message = _("'{category}' is not a category: no placeholder, not empty")
            message = message.format(category=category)
            raise ValueError(message)
        check_layout(category)
