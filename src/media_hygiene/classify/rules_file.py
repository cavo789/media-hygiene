"""Add, replace or remove a `[[classify.rules]]` rule in `config.toml`, comments kept.

The review-sort page writes the rules the user validates there (0392, 0393). `tomlkit`
edits the document in place and the file is replaced atomically (`places/toml_edit`);
each change is read back from the disk and returned as the file holds it. A new rule
goes just above *Existing folders* (the list's order decides: the first sure rule
wins), the comments kept above the rule they were written for.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import AoT, Comment, Table, Whitespace

from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _
from media_hygiene.places.toml_edit import (
    ENCODING,
    document_of,
    table_of,
    write_document,
)

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

_SECTION: Final = "classify"
_RULES: Final = "rules"


def read_rules(config_file: Path) -> tuple[ClassifyRule, ...]:
    """The rules the file holds, as `classify` reads them.

    Args:
        config_file: `config.toml`.

    Returns:
        The rules, in the file's order; none when the file has no list.
    """
    if not config_file.is_file():
        return ()
    loaded = tomllib.loads(config_file.read_text(ENCODING))
    written = loaded.get(_SECTION, {}).get(_RULES, [])
    return tuple(ClassifyRule.model_validate(item) for item in written)


def add_rule(config_file: Path, rule: ClassifyRule) -> ClassifyRule:
    """Write a rule just above *Existing folders*, then read it back.

    Args:
        config_file: `config.toml`, holding the list of rules.
        rule: The rule, checked.

    Returns:
        The rule, as the file holds it now.

    Raises:
        ConfigError: The file holds no list of rules, a rule has the same name, or the
            rule read back is not the one written.
    """
    document = document_of(config_file)
    rules = rules_of(document)
    if any(named(item, rule.name) for item in rules):
        message = _("A rule is already named '{name}' in config.toml.")
        raise ConfigError(message.format(name=rule.name))
    at = next(
        (
            index
            for index, item in enumerate(rules)
            if item.get("match") == RuleMatch.EXISTING_FOLDER.value
        ),
        0,
    )
    table = rule_table(rule)
    if at > 0:
        _move_tail(rules[at - 1], table)
    rules.insert(at, table)
    write_document(config_file, document)
    return read_back(config_file, rule)


def rules_of(document: TOMLDocument) -> AoT:
    """The list of rules of the document.

    Args:
        document: `config.toml`.

    Returns:
        Its `[[classify.rules]]`.

    Raises:
        ConfigError: The file holds none: `classify` then uses its example list, which
            the page cannot extend without writing it whole.
    """
    found = table_of(document, _SECTION).get(_RULES)
    if not isinstance(found, AoT):
        message = _("config.toml holds no [[classify.rules]]: write one first.")
        raise ConfigError(message)
    return found


def named(item: Table, name: str) -> bool:
    """Tell whether a rule of the file carries a name, case ignored.

    Args:
        item: A rule of the file.
        name: The name.

    Returns:
        True when it does.
    """
    return str(item.get("name", "")).casefold() == name.casefold()


def rule_table(rule: ClassifyRule) -> Table:
    """A rule as a TOML table: its fields set, in the model's order.

    Args:
        rule: The rule.

    Returns:
        The table, a blank line after it.
    """
    table = tomlkit.table()
    for key, value in rule.model_dump(mode="json", exclude_defaults=True).items():
        table[key] = value
    table.add(tomlkit.nl())
    return table


def _move_tail(before: Table, table: Table) -> None:
    """Move the comments written above the next rule from the one before to the new one.

    tomlkit keeps the comments above a `[[classify.rules]]` in the table before it: a
    rule inserted there would come between a comment and its rule.

    Args:
        before: The rule the new one follows.
        table: The new rule.
    """
    body = before.value.body
    tail: list[tuple[None, Comment | Whitespace]] = []
    trivia = (Comment, Whitespace)
    while body and body[-1][0] is None and isinstance(body[-1][1], trivia):
        tail.insert(0, body.pop())  # type: ignore[arg-type]
    while tail and isinstance(tail[0][1], Whitespace):
        body.append(tail.pop(0))  # the blank line stays where it was
    table.value.body.extend(tail)


def read_back(config_file: Path, rule: ClassifyRule) -> ClassifyRule:
    """Find the rule in the file just written.

    Args:
        config_file: `config.toml`.
        rule: The rule written.

    Returns:
        It, as read from the disk.

    Raises:
        ConfigError: The file does not hold it.
    """
    held = next((item for item in read_rules(config_file) if item == rule), None)
    if held is None:
        message = _("config.toml read back does not hold the rule '{name}'.")
        raise ConfigError(message.format(name=rule.name))
    return held
