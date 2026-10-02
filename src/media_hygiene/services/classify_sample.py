"""`classify --sample N`: describe N random photos, time it, before a long run.

The photos come from those a full run would ask about, not described yet; what they
cost per photo, describing then mapping, gives the estimate of the full run. Their
descriptions stay in the cache: the full run will not describe them again.
"""

from __future__ import annotations

import secrets
import statistics
import time
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.classify_subjects import SubjectStep
    from media_hygiene.services.subject_answers import Answering
    from media_hygiene.services.subject_plan import SubjectPlan


@dataclass(frozen=True, slots=True)
class SampleRow:
    """One photo of the sample: what the model saw, the category it chose."""

    path: Path
    description: str
    category: str  # of the first `subject` rule; empty: none fits, or no rule


@dataclass(frozen=True, slots=True)
class SampleResult:
    """The sample, its cost per photo, and what a full run would still describe."""

    rows: tuple[SampleRow, ...]
    describe_seconds: float  # per photo
    map_seconds: float  # per photo
    to_describe: int

    @property
    def total(self) -> float:
        """The estimated time of a full run.

        Returns:
            Seconds.
        """
        return self.to_describe * (self.describe_seconds + self.map_seconds)


def run_sample(
    step: SubjectStep, plan: SubjectPlan, request: tuple[int, Answering]
) -> SampleResult:
    """Describe and map a random sample of the photos a full run would ask about.

    Args:
        step: The open subject step.
        plan: The plan of the full run.
        request: How many photos, and progress and Ctrl+C.

    Returns:
        The sample and its timings.
    """
    count, answering = request
    candidates = dict.fromkeys(c.path for unit in plan.units for c in unit.candidates)
    fresh = [path for path in candidates if step.store.get(plan.versions[path]) is None]
    chosen = secrets.SystemRandom().sample(fresh, min(count, len(fresh)))
    if chosen:
        step.describe([plan.versions[path] for path in chosen], answering)
    found = {
        path: description
        for path in chosen
        if (description := step.store.get(plan.versions[path])) is not None
    }
    categories: dict[Path, str] = {}
    map_seconds = 0.0
    if plan.rules and found:
        started = time.monotonic()
        sample_plan = replace(plan, samples={"": tuple(found)})
        categories = step.map(sample_plan, plan.rules[0], answering.progress)
        map_seconds = (time.monotonic() - started) / len(found)
    timed = [d.seconds for d in found.values() if d.seconds > 0]
    return SampleResult(
        tuple(
            SampleRow(path, d.text, categories.get(path, ""))
            for path, d in found.items()
        ),
        statistics.mean(timed) if timed else plan.seconds_per_photo,
        map_seconds,
        sum(1 for photo in plan.missing if photo.path not in found),
    )
