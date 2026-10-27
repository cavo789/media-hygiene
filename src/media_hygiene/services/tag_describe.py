"""`tags` and the vision model: describe what the cache lacks, or a timed sample.

Each answer is committed at once: Ctrl+C keeps what is done, and the next run goes
on. `--sample N` describes N of the photos a full run would send, at random, and
tells what the full run would cost; its answers stay in the cache.
"""

from __future__ import annotations

import secrets
import statistics
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.classify.ai.client import OllamaClient
from media_hygiene.services.describing import DescribeJob, describe_checked
from media_hygiene.services.tag_derive import TaggingStore
from media_hygiene.tags.normalize import normalize
from media_hygiene.tags.vision import tags_question

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.ai.describe import DescribeOutcome
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
    step: TagStep, work: TagWork, answering: Answering
) -> DescribeOutcome:
    """Describe the photos the cache lacks, after checking that the model sees images.

    Args:
        step: The open tag step: settings, cache, pool.
        work: The photos missing, in the order to describe them, and the frame of
            each video among them.
        answering: Progress and Ctrl+C.

    Returns:
        How it went.

    Raises:
        AiError: The model cannot be reached, or cannot see images.
    """
    client = OllamaClient(step.runtime.settings.classify.ai)
    question = tags_question(step.rules.language)
    # Each answer writes its words at once: searchable while the run goes (0353).
    store = TaggingStore(step.store, work, step.sight)
    store.telling(answering.progress.current)  # the last photo's words (0421)
    job = DescribeJob(client, store, answering, question, work.stills)
    return describe_checked(step.runtime, work.missing, job)


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
        describe_photos(step, replace(work, missing=tuple(chosen)), answering)
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
