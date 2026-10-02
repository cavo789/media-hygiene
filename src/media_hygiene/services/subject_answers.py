"""How the `subject` rules are answered, and the categories one rule gives."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.classify.ai.describe import DescribeOutcome
from media_hygiene.classify.ai.mapping import map_all
from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.classify.ai.mapping import MapDeps
    from media_hygiene.classify.ai.models import Subject
    from media_hygiene.config.classify_rules import ClassifyRule
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.subject_plan import SubjectPlan


@dataclass(frozen=True, slots=True)
class Answering:
    """How to answer: describe or use the cache only, where to show progress."""

    describe: bool
    progress: ProgressSink
    stopped: Callable[[], bool] = lambda: False


@dataclass(frozen=True, slots=True)
class Answered:
    """The subjects of every `subject` rule, and how describing went."""

    subjects: dict[str, dict[Path, Subject]]
    outcome: DescribeOutcome = field(default_factory=DescribeOutcome)


def answers_of(plan: SubjectPlan, rule: ClassifyRule, deps: MapDeps) -> dict[Path, str]:
    """Map the described samples of a plan to the categories of one rule.

    Samples never described (no model, `--no-describe`, Ctrl+C) give no answer.

    Args:
        plan: The plan: the samples and their versions.
        rule: The rule.
        deps: Model, cache, progress.

    Returns:
        The category of each described sample (empty: none fits).
    """
    found = {
        path: description
        for paths in plan.samples.values()
        for path in paths
        if (description := deps.store.get(plan.versions[path])) is not None
    }
    if not found:
        return {}
    deps.progress.start(Step(_("Choosing categories"), rule.name), None)
    try:
        summaries = [d.summary for d in found.values()]
        chosen = asyncio.run(map_all(summaries, rule.categories, deps))
    finally:
        deps.progress.stop()
    return {path: chosen[d.summary] for path, d in found.items() if d.summary in chosen}
