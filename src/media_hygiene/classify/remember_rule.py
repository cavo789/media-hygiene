"""*Remember as a rule*: its `date_range` rule goes to `events/<year>.toml` (0578).

One place for what the tool remembers (0576); `config.toml` stays the user's: a folder
rule turned into dates (0393) leaves it for `events/` too (0611), removed with tomlkit,
the comments of the file kept.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.classify.event_store import add_event, holder, replace_event
from media_hygiene.classify.rules_edit import remove_rules
from media_hygiene.errors import ConfigError
from media_hygiene.file_history import replace_text

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.classify_rules import ClassifyRule

_ENCODING: Final = "utf-8"  # what tomlkit writes


def remember_rule(config: Path, replaces: str, rule: ClassifyRule) -> ClassifyRule:
    """Write a `date_range` rule where the tool keeps what it remembers (0578).

    Args:
        config: `config.toml`, beside `events/`.
        replaces: The rule it takes the place of (0393), or empty.
        rule: The rule.

    Returns:
        It, as the files hold it now.

    Raises:
        ConfigError: The event cannot be written; `config.toml` is then put back.
    """
    if not replaces:
        return add_event(config, rule)
    if holder(config.parent, replaces) is not None:
        return replace_event(config, replaces, rule)
    before = config.read_bytes()  # a folder rule of the user's file moves (0611)
    remove_rules(config, [replaces])
    try:
        return add_event(config, rule)
    except ConfigError:
        # Put back atomically, as every save of the file (0778): the state the
        # failed write left is kept as a version, never half written over.
        replace_text(config, before.decode(_ENCODING))
        raise
