"""Write the events the tool remembers into `/config/events/<year>.toml` (0576).

A new event goes to the file of the year it starts in; a changed or removed one is
changed in the file that holds it, whatever its name (a file renamed by hand keeps its
events). Same editing as `rules_file`: tomlkit (comments kept), atomic, read back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tomlkit
from tomlkit.items import AoT

from media_hygiene.classify.rules.calendar import parse_one_off
from media_hygiene.classify.rules_file import named, read_back, read_rules, rule_table
from media_hygiene.config.event_layer import FOLDER, RULES, event_files, read_file
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _
from media_hygiene.places.toml_edit import document_of, write_document

if TYPE_CHECKING:
    from collections.abc import Collection
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

    from media_hygiene.config.classify_rules import ClassifyRule


def year_file(config_dir: Path, rule: ClassifyRule) -> Path:
    """The file a new event goes to: the year it starts in.

    Args:
        config_dir: The folder of `config.toml`.
        rule: The event (`date_range`).

    Returns:
        `events/<year>.toml`.
    """
    year = parse_one_off(rule.dates).start.year
    return config_dir / FOLDER / f"{year}.toml"


def holder(config_dir: Path, name: str) -> Path | None:
    """The events file holding an event, case ignored.

    Args:
        config_dir: The folder of `config.toml`.
        name: The event's name.

    Returns:
        The file; None when no events file holds it.
    """
    folded = name.casefold()
    return next(
        (
            path
            for path in event_files(config_dir)
            if any(
                str(item.get("name", "")).casefold() == folded
                for item in read_file(path)
            )
        ),
        None,
    )


def add_event(config_file: Path, rule: ClassifyRule) -> ClassifyRule:
    """Write a new event into the file of its year, then read it back.

    Args:
        config_file: `config.toml`, beside the folder `events/`.
        rule: The event.

    Returns:
        The event, as the files hold it now.

    Raises:
        ConfigError: A rule or an event has the same name, or the event read back is
            not the one written.
    """
    if any(
        item.name.casefold() == rule.name.casefold() for item in read_rules(config_file)
    ):
        message = _("A rule is already named '{name}' in config.toml.")
        raise ConfigError(message.format(name=rule.name))
    path = year_file(config_file.parent, rule)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = document_of(path)
    _rules_of(document).append(rule_table(rule))
    write_document(path, document)
    return read_back(config_file, rule)


def replace_event(config_file: Path, name: str, rule: ClassifyRule) -> ClassifyRule:
    """Put an event in the place of another one, in the file holding it, read back.

    Args:
        config_file: `config.toml`.
        name: The event replaced.
        rule: The new one.

    Returns:
        The new event, as the files hold it.

    Raises:
        ConfigError: No events file holds the name, or another rule has the new name.
    """
    path = holder(config_file.parent, name)
    if path is None:
        message = _("config.toml holds no rule named '{name}'.").format(name=name)
        raise ConfigError(message)
    others = (item for item in read_rules(config_file) if not _same(item.name, name))
    if any(_same(item.name, rule.name) for item in others):
        message = _("A rule is already named '{name}' in config.toml.")
        raise ConfigError(message.format(name=rule.name))
    document = document_of(path)
    rules = _rules_of(document)
    at = next(index for index, item in enumerate(rules) if named(item, name))
    rules[at] = rule_table(rule)
    write_document(path, document)
    return read_back(config_file, rule)


def remove_events(config_dir: Path, names: Collection[str]) -> None:
    """Remove events by name from the files holding them.

    Args:
        config_dir: The folder of `config.toml`.
        names: The events' names; a name no events file holds is ignored.
    """
    for path in event_files(config_dir):
        document = document_of(path)
        rules = _rules_of(document)
        found = [
            i for i, item in enumerate(rules) if any(named(item, n) for n in names)
        ]
        for index in reversed(found):
            del rules[index]
        if found:
            write_document(path, document)


def write_events(config_dir: Path, rules: Collection[ClassifyRule]) -> None:
    """Append events to the files of their years, no check of names (`config tidy`).

    Args:
        config_dir: The folder of `config.toml`.
        rules: The events moved out of `config.toml`.
    """
    for path in sorted({year_file(config_dir, rule) for rule in rules}):
        path.parent.mkdir(parents=True, exist_ok=True)
        document = document_of(path)
        held = _rules_of(document)
        for rule in rules:
            if year_file(config_dir, rule) == path and not any(
                named(item, rule.name) for item in held
            ):
                held.append(rule_table(rule))
        write_document(path, document)


def _rules_of(document: TOMLDocument) -> AoT:
    """The `[[rules]]` of an events file, added when missing.

    Args:
        document: The file.

    Returns:
        Its list of events.
    """
    found = document.get(RULES)
    if isinstance(found, AoT):
        return found
    created = tomlkit.aot()
    document[RULES] = created
    return created


def _same(one: str, other: str) -> bool:
    """Tell whether two names are the same, case ignored.

    Args:
        one: A name.
        other: Another.

    Returns:
        True when they are.
    """
    return one.casefold() == other.casefold()
