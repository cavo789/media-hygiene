"""*Remember as a rule*: its `date_range` rule goes to `events/<year>.toml` (0578).

One place for what the tool remembers (0576); `config.toml` stays the user's: only a
folder rule turned into dates (0393) is still replaced where the user wrote it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.event_store import add_event, holder, replace_event
from media_hygiene.classify.rules_edit import replace_rule

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.classify_rules import ClassifyRule


def remember_rule(config: Path, replaces: str, rule: ClassifyRule) -> ClassifyRule:
    """Write a `date_range` rule where the tool keeps what it remembers (0578).

    Args:
        config: `config.toml`, beside `events/`.
        replaces: The rule it takes the place of (0393), or empty.
        rule: The rule.

    Returns:
        It, as the files hold it now.
    """
    if not replaces:
        return add_event(config, rule)
    if holder(config.parent, replaces) is not None:
        return replace_event(config, replaces, rule)
    return replace_rule(config, replaces, rule)  # a folder rule of the user's file
