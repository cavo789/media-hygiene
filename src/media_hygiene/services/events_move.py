"""`config tidy`: move the events the tool wrote in `config.toml` to `events/` (0576).

Before 0576, *Move to an event…* and *Events found in your folders* wrote each event as
a `[[classify.rules]]` block of `config.toml`. `config tidy` lists them (read-only) and,
with `--apply`, copies `config.toml` to `/cache/config-backups/` first, writes the
events into `events/<year>.toml`, then removes them from `config.toml`; both are read
back. An event is a `date_range` rule shaped as the tool writes it: its category is its
name, or its name is the category followed by ` (…)`. Hand-written rules stay in
`config.toml`. Cut short between the two writes, the events are in both places:
`config.toml` wins (`event_layer`) and the next `config tidy --apply` finishes the move.
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from media_hygiene.classify.event_store import holder, write_events
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.rules_edit import remove_rules
from media_hygiene.classify.rules_file import read_written
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _
from media_hygiene.services.config_tidy import BACKUP_DIR, writable

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.classify_rules import ClassifyRule
    from media_hygiene.services.runtime import Runtime

_STAMP = "%Y%m%d-%H%M%S"


def events_to_move(config_file: Path) -> tuple[ClassifyRule, ...]:
    """The events the tool wrote in `config.toml`.

    Args:
        config_file: `config.toml`.

    Returns:
        Them, in the file's order; none without the file.
    """
    return tuple(rule for rule in read_written(config_file) if _written_by_tool(rule))


def move_events(runtime: Runtime, rules: tuple[ClassifyRule, ...]) -> Path:
    """Copy `config.toml` aside, move the events to `events/`, read both back.

    Args:
        runtime: Settings, mount points and output.
        rules: The events to move.

    Returns:
        The copy of `config.toml` kept.

    Raises:
        ConfigError: An event is not in `events/` once written.
    """
    writable(runtime)
    config_file = runtime.locations.config_file
    backups = runtime.locations.cache_dir / BACKUP_DIR
    backups.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime(_STAMP)
    backup = backups / f"{config_file.name}.bak-{stamp}-events"
    shutil.copy2(config_file, backup)
    write_events(config_file.parent, rules)
    if any(holder(config_file.parent, rule.name) is None for rule in rules):
        raise ConfigError(
            _("An event was not found in the events folder once written.")
        )
    remove_rules(config_file, [rule.name for rule in rules])
    return backup


def _written_by_tool(rule: ClassifyRule) -> bool:
    """Tell whether a rule has the shape of an event the tool remembers.

    Args:
        rule: A rule of `config.toml`.

    Returns:
        True for a `date_range` rule named after its category.
    """
    if rule.match is not RuleMatch.DATE_RANGE or not rule.category:
        return False
    return rule.name == rule.category or rule.name.startswith(f"{rule.category} (")
