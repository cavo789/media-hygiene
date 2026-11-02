"""Remove rules that decide nothing, or turn one into another, in `config.toml` (0393).

The *Your rules* dialog of the review-sort page cleans the list (a rule that matches
nothing any more is removed) and turns a folder-name rule (`path`) into a date rule in
its place: the list's order decides which rule wins. Same editing as `rules_file`:
tomlkit, comments kept, atomic, read back from the disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tomlkit.items import AoT, Comment, Table, Whitespace

from media_hygiene.classify.event_store import holder, remove_events, replace_event
from media_hygiene.classify.rules_file import (
    named,
    read_back,
    read_rules,
    read_written,
    rule_table,
    rules_of,
)
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _
from media_hygiene.places.toml_edit import document_of, write_document

if TYPE_CHECKING:
    from collections.abc import Collection
    from pathlib import Path

    from media_hygiene.config.classify_rules import ClassifyRule


def remove_rules(config_file: Path, names: Collection[str]) -> tuple[ClassifyRule, ...]:
    """Remove rules by name, then read the list back.

    Args:
        config_file: `config.toml`.
        names: The rules to remove.

    Returns:
        The rules the file holds now.

    Raises:
        ConfigError: A name is not in the file, or one is still there once written.
    """
    events = {
        n for n in names if not _written(config_file, n) and _event(config_file, n)
    }
    remove_events(config_file.parent, events)
    names = [name for name in names if name not in events]
    if names:
        document = document_of(config_file)
        rules = rules_of(document)
        found = [
            index
            for index, item in enumerate(rules)
            if any(named(item, name) for name in names)
        ]
        if len(found) != len(set(names)):
            raise ConfigError(_("config.toml holds no rule of one of these names."))
        for index in reversed(found):
            _remove(rules, index)
        write_document(config_file, document)
    still = any(_any_rule(rule, names) for rule in read_written(config_file))
    if still or any(_event(config_file, name) for name in events):
        raise ConfigError(_("config.toml read back still holds a rule removed."))
    return read_rules(config_file)


def replace_rule(config_file: Path, name: str, rule: ClassifyRule) -> ClassifyRule:
    """Put a rule in the place of another one, then read it back.

    Args:
        config_file: `config.toml`.
        name: The rule replaced.
        rule: The new one.

    Returns:
        The new rule, as the file holds it.

    Raises:
        ConfigError: No rule has that name, or another one already has the new name.
    """
    if not _written(config_file, name) and _event(config_file, name):
        return replace_event(config_file, name, rule)  # an event of `events/` (0576)
    document = document_of(config_file)
    rules = rules_of(document)
    at = next((index for index, item in enumerate(rules) if named(item, name)), None)
    if at is None:
        message = _("config.toml holds no rule named '{name}'.").format(name=name)
        raise ConfigError(message)
    if any(named(item, rule.name) for index, item in enumerate(rules) if index != at):
        message = _("A rule is already named '{name}' in config.toml.")
        raise ConfigError(message.format(name=rule.name))
    tail = _tail(rules[at])  # the blank lines and the comments above the next rule
    table = rule_table(rule)
    if tail:
        table.value.body.pop()  # its own blank line: those of the file are kept
    table.value.body.extend(tail)
    rules[at] = table
    write_document(config_file, document)
    return read_back(config_file, rule)


def _written(config_file: Path, name: str) -> bool:
    """Tell whether `config.toml` itself holds a rule of that name, case ignored.

    Args:
        config_file: `config.toml`.
        name: The name.

    Returns:
        True when it does.
    """
    return any(_any_rule(rule, (name,)) for rule in read_written(config_file))


def _event(config_file: Path, name: str) -> bool:
    """Tell whether an events file of `events/` holds that name.

    Args:
        config_file: `config.toml`.
        name: The name.

    Returns:
        True when one does.
    """
    return holder(config_file.parent, name) is not None


def _any_rule(rule: ClassifyRule, names: Collection[str]) -> bool:
    """Tell whether a rule carries one of the names, case ignored.

    Args:
        rule: A rule read back.
        names: The names.

    Returns:
        True when it does.
    """
    return rule.name.casefold() in {name.casefold() for name in names}


def _remove(rules: AoT, index: int) -> None:
    """Remove one rule; its comments go with it, those of the next rule stay.

    tomlkit keeps the comments above a rule in the rule before it: those above the rule
    removed are dropped from the one before, the ones it held move there.

    Args:
        rules: The list of rules.
        index: The rule to remove.
    """
    tail = _tail(rules[index])
    if index > 0:
        before = _tail(rules[index - 1])
        body = rules[index - 1].value.body
        if not tail or not isinstance(tail[0][1], Whitespace):  # one blank line only
            body.extend(entry for entry in before if isinstance(entry[1], Whitespace))
        body.extend(tail)
    del rules[index]


def _tail(table: Table) -> list[tuple[None, Comment | Whitespace]]:
    """Take the blank lines and comments ending a rule: those of the next rule.

    Args:
        table: A rule of the file.

    Returns:
        Them, in order, taken out of the rule.
    """
    body = table.value.body
    tail: list[tuple[None, Comment | Whitespace]] = []
    trivia = (Comment, Whitespace)
    while body and body[-1][0] is None and isinstance(body[-1][1], trivia):
        tail.insert(0, body.pop())  # type: ignore[arg-type]
    return tail
