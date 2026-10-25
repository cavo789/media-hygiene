"""The `person` rules of a `classify` run: their names checked, then who is on photos.

The names of a rule must be people of `[[people.person]]` (case and accents aside): a
rule naming nobody is refused before anything is read, naming itself. The people of
each photo are then read once from the faces of the index, as `search` reads them.
Without a `person` rule, nothing is read.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _
from media_hygiene.index.read_only import connect_read_only
from media_hygiene.people.folding import folded
from media_hygiene.search.people_words import people_words
from media_hygiene.services.data_checks import unreadable_index

if TYPE_CHECKING:
    from media_hygiene.classify.engine import Scope
    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.config.settings import Settings
    from media_hygiene.services.runtime import Runtime


def with_people(scope: Scope, runtime: Runtime) -> Scope:
    """Add the people named, and who is on each photo when a `person` rule needs it.

    Args:
        scope: The scope of the run.
        runtime: Settings, mount points.

    Returns:
        The scope, with the names of `[[people.person]]` (their folders are theirs)
        and the names on each photo of the index.

    Raises:
        MountError: The index cannot be read.
    """
    named = tuple(person.name for person in runtime.settings.people.person)
    scope = replace(scope, people=named)
    if not check_people(runtime.settings):
        return scope
    index = runtime.index_file
    if index is None or not index.is_file():
        return scope
    try:
        with closing(connect_read_only(index)) as connection:
            people = people_words(connection, runtime.settings.people)
    except sqlite3.Error as exc:
        raise unreadable_index(runtime, index, exc) from exc
    return replace(scope, seen=replace(scope.seen, people=people))


def check_people(settings: Settings) -> bool:
    """Refuse a `person` rule that names someone `[[people.person]]` does not.

    Args:
        settings: The settings of the run.

    Returns:
        True when at least one `person` rule is written.

    Raises:
        ConfigError: A rule names nobody known; the first one is said.
    """
    rules = [r for r in settings.classify.rules if r.match is RuleMatch.PERSON]
    known = {folded(person.name) for person in settings.people.person}
    for rule in rules:
        unknown = [name for name in rule.names if folded(name) not in known]
        if unknown:
            raise ConfigError(_unknown(rule.name, unknown, settings.people), _tip())
    return bool(rules)


def _unknown(rule: str, unknown: list[str], people: PeopleSettings) -> str:
    """Say which names of a rule name nobody, and who is named.

    Args:
        rule: The rule's name.
        unknown: Its names nobody has.
        people: `[people]`, with the names.

    Returns:
        The sentence.
    """
    names = ", ".join(f'"{name}"' for name in unknown)
    text = _("Rule '{rule}': nobody is named {names} in [[people.person]].").format(
        rule=rule, names=names
    )
    if not people.person:
        return f"{text} {_('Nobody is named yet.')}"
    named = ", ".join(person.name for person in people.person)
    return f"{text} {_('Named: {names}.').format(names=named)}"


def _tip() -> str:
    """How to fix an unknown name.

    Returns:
        The tip.
    """
    return _(
        "Name their group on the 'people' page first, or correct the names of the "
        "rule in config.toml."
    )
