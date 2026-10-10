"""`tags` and the vision model: describe what the cache lacks, or a timed sample.

Each answer is committed at once: Ctrl+C keeps what is done, and the next run goes
on. `--sample N` describes N of the photos a full run would send, at random, and
tells what the full run would cost; its answers stay in the cache.
"""

from __future__ import annotations

import asyncio
import secrets
import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.ai.client import OllamaClient
from media_hygiene.classify.ai.describe import DescribeDeps, describe_all
from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step
from media_hygiene.tags.normalize import normalize
from media_hygiene.tags.vision import tags_question

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.classify.ai.describe import DescribeOutcome
    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.services.subject_answers import Answering
    from media_hygiene.services.tag_work import TagWork
    from media_hygiene.services.tags import TagStep


@dataclass(frozen=True, slots=True)
class TagSampleRow:
    """One photo of the sample: the model's sentence, its tags, its time."""

    path: Path
    sentence: str
    tags: tuple[str, ...]
    seconds: float


@dataclass(frozen=True, slots=True)
class TagSample:
    """The sample, the time per photo, and what a full run would still describe."""

    rows: tuple[TagSampleRow, ...]
    seconds_per_photo: float
    to_describe: int

    @property
    def total(self) -> float:
        """The estimated time of a full run.

        Returns:
            Seconds.
        """
        return self.to_describe * self.seconds_per_photo


def describe_photos(
    step: TagStep, photos: Sequence[PhotoVersion], answering: Answering
) -> DescribeOutcome:
    """Describe photos, after checking that the model sees images.

    Args:
        step: The open tag step: settings, cache, pool.
        photos: The photos, in the order to describe them.
        answering: Progress and Ctrl+C.

    Returns:
        How it went.

    Raises:
        AiError: The model cannot be reached, or cannot see images.
    """
    runtime = step.runtime
    settings = runtime.settings.classify.ai
    client = OllamaClient(settings)
    asyncio.run(client.require_vision(settings.model))
    progress = answering.progress
    with runtime.executor_factory() as executor:
        deps = DescribeDeps(
            client,
            step.store,
            executor,
            progress,
            answering.stopped,
            tags_question(step.rules.language),
        )
        progress.start(Step(_("Describing photos"), settings.model), len(photos))
        try:
            outcome = asyncio.run(describe_all(photos, deps))
        finally:
            progress.stop()
    if outcome.errors:
        raise outcome.errors[0]
    return outcome


def run_tag_sample(
    step: TagStep, work: TagWork, request: tuple[int, Answering]
) -> TagSample:
    """Describe a random sample of the photos a full run would send.

    Args:
        step: The open tag step.
        work: The work of the full run.
        request: How many photos, and progress and Ctrl+C.

    Returns:
        The sample and its timings.
    """
    count, answering = request
    chosen = secrets.SystemRandom().sample(
        list(work.missing), min(count, len(work.missing))
    )
    if chosen:
        describe_photos(step, chosen, answering)
    rows = tuple(
        TagSampleRow(
            photo.path,
            found.text,
            normalize(found.tags, step.rules),
            found.seconds,
        )
        for photo in chosen
        if (found := step.store.get(photo)) is not None
    )
    timed = [row.seconds for row in rows if row.seconds > 0]
    return TagSample(
        rows,
        statistics.mean(timed) if timed else work.seconds_per_photo,
        len(work.missing) - len(rows),
    )
