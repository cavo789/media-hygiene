"""A date rule tried on the photos of its days (0396): the classify engine, no write.

The search page sends a period and a rule typed in its dialog; the files of those days
(and of the day before and after: an evening that ends after midnight stays one event)
are read from the index and given to `classify` with the rules of `config.toml`, the
rule tried put where saving it would (above *Existing folders*, or in place of the
rule it replaces). Each file then says where `sort` would put it and which rule
decides: those the rule takes, those of its days it leaves to another (0394).
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.classify.engine import classify
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.rules_file import read_rules
from media_hygiene.index.former_names import former_of
from media_hygiene.index.listing import deepest_first
from media_hygiene.index.rows import facts_of
from media_hygiene.index.schema import SELECT
from media_hygiene.index.takeout_rows import takeout_of
from media_hygiene.scan.filters import media_kind
from media_hygiene.search.rule_models import Tried
from media_hygiene.services.classify_inputs import input_of, root_of, with_takeout
from media_hygiene.services.classify_people import with_people
from media_hygiene.services.classify_scope import run_scope

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.config.classify_rules import ClassifyRule
    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.search.rule_models import RuleTry
    from media_hygiene.services.runtime import Runtime


def try_rule(
    runtime: Runtime, connection: sqlite3.Connection, asked: RuleTry
) -> dict[Path, Tried]:
    """Classify the files given with the rule tried among the rules of `config.toml`.

    Args:
        runtime: Settings, mount points.
        connection: The open index (read only).
        asked: The rule, the rule it replaces, the files.

    Returns:
        By container path, where each file would go.
    """
    files = _inputs(runtime, connection, asked.files)
    settings = runtime.settings.classify
    rules = tried_rules(written_rules(runtime), asked.rule, asked.replaces)
    scope = with_people(run_scope(runtime, None), runtime)
    found = classify(files, settings.model_copy(update={"rules": rules}), scope)
    name = asked.rule.name
    spans = {
        event.event_id: (
            event.start.date().isoformat(),
            event.end.date().isoformat(),
            len(event.paths),
        )
        for event in found.events
    }
    return {
        proposal.file.path: Tried(
            proposal.folder,
            proposal.rule,
            proposal.rule == name,
            spans.get(proposal.event_id),
        )
        for proposal in found.proposals
    }


def tried_rules(
    rules: Sequence[ClassifyRule], rule: ClassifyRule, replaces: str
) -> tuple[ClassifyRule, ...]:
    """The rules with the one tried where saving it would put it.

    Args:
        rules: The rules of `config.toml`.
        rule: The rule tried.
        replaces: The name of the rule it replaces; empty: a new rule.

    Returns:
        In place of the rule replaced; else just above *Existing folders* (last when
        there is none). A rule of the same name is left out.
    """
    if replaces and any(other.name == replaces for other in rules):
        return tuple(rule if other.name == replaces else other for other in rules)
    others = [other for other in rules if other.name != rule.name]
    at = next(
        (
            index
            for index, other in enumerate(others)
            if other.match is RuleMatch.EXISTING_FOLDER
        ),
        len(others),
    )
    return (*others[:at], rule, *others[at:])


def written_rules(runtime: Runtime) -> tuple[ClassifyRule, ...]:
    """The rules `config.toml` holds now: the page may have saved one since it opened.

    Args:
        runtime: Settings, mount points.

    Returns:
        The file's rules; the settings' when there is no file.
    """
    config = runtime.locations.config_file
    return read_rules(config) if config.is_file() else runtime.settings.classify.rules


def _inputs(
    runtime: Runtime, connection: sqlite3.Connection, files: Sequence[PhotoVersion]
) -> tuple[MediaInput, ...]:
    """What `classify` needs of the files, from the index.

    Args:
        runtime: Mount points.
        connection: The open index.
        files: The files, as the search found them.

    Returns:
        One input per media file, its facts as the index holds them.
    """
    roots = deepest_first(connection)
    found: list[MediaInput] = []
    for file in files:
        row = connection.execute(SELECT, (str(file.path),)).fetchone()
        if row is None or media_kind(file.path) is None:
            continue
        item = input_of(file, root_of(file.path, roots, runtime), facts_of(row))
        item = replace(item, former=former_of(connection, file.path))
        found.append(with_takeout(item, takeout_of(connection, file.path)))
    return tuple(found)
