"""The ordered rules of `[[classify.rules]]`: the first sure match decides.

Each file is read against the rules, in order. The first match whose score reaches
`sure` wins; otherwise the best match (the earliest on a tie) is a guess to check.
`other_category` takes the files no rule above it matched. A score of 0 turns a rule
off. A date rule reads the event: when at least half of an event's files fall in its
dates, the whole event takes it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.layout import Values, render
from media_hygiene.classify.rules.building import build_test
from media_hygiene.classify.rules.kinds import BUILT_IN, REASONS, RuleMatch
from media_hygiene.classify.signals import NO_SIGNAL, Signal

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.classify.rules.building import RuleFacts
    from media_hygiene.classify.rules.matchers import Test
    from media_hygiene.config.classify_rules import ClassifyRule
    from media_hygiene.config.classify_settings import ClassifySettings


def decide(
    files: Sequence[MediaInput], settings: ClassifySettings, facts: RuleFacts
) -> dict[Path, Signal]:
    """Read every file against the rules.

    Args:
        files: The files.
        settings: `[classify]`: the rules, their scores and `sure`.
        facts: Dates, folder signals, events, host paths.

    Returns:
        The signal of each file: its category, reason, rule and score.
    """
    rules = tuple((rule, build_test(rule, facts)) for rule in settings.rules)
    return {file.path: _first(file, rules, (settings, facts)) for file in files}


def _first(
    file: MediaInput,
    rules: tuple[tuple[ClassifyRule, Test], ...],
    config: tuple[ClassifySettings, RuleFacts],
) -> Signal:
    """The signal of the rule that decides one file.

    Args:
        file: The file.
        rules: The rules and their tests, in order.
        config: `[classify]` and the facts.

    Returns:
        The first sure match, else the best match, else no signal.
    """
    settings = config[0]
    best: Signal | None = None
    for rule, test in rules:
        fallback = rule.match is RuleMatch.OTHER_CATEGORY
        if (fallback and best is not None) or not test(file):
            continue
        signal = _signal(rule, file, config)
        score = signal.score or 0
        if score <= 0:
            continue
        if fallback or score >= settings.sure:
            return signal
        if best is None or score > (best.score or 0):
            best = signal
    return best or NO_SIGNAL


def _signal(
    rule: ClassifyRule, file: MediaInput, config: tuple[ClassifySettings, RuleFacts]
) -> Signal:
    """What a matching rule says of one file.

    Args:
        rule: The rule.
        file: The file.
        config: `[classify]` and the facts.

    Returns:
        Its signal; the built-in rules give the folders' category.
    """
    settings, facts = config
    if rule.match in BUILT_IN:
        folder = facts.folders[file.path]
        reason, category, stay = folder.reason, folder.category, False
    else:
        reason, stay = REASONS[rule.match], not rule.category
        category = _category(rule.category, file, facts)
    score = rule.score
    if score is None:
        score = settings.scores.get(reason.value, 0)
    return Signal(reason, category, rule.name, score, stay)


def _category(template: str, file: MediaInput, facts: RuleFacts) -> str:
    """Render a rule's category: its placeholders take the event's start date.

    Args:
        template: E.g. `Parties/Christmas {year}`.
        file: The file.
        facts: Its date and event.

    Returns:
        The category, folder-safe; empty when the rule gives none.
    """
    event = facts.event_of.get(file.path)
    when = event.start if event else facts.datings[file.path].when
    values = Values(
        year=when.year,
        month=when.month,
        day=when.day,
        event=(event.label or event.span) if event else "",
        event_start=event.start.date().isoformat() if event else "",
    )
    return render(template, values) or ""
