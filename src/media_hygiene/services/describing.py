"""Describe photos with the local vision model, once it proved it sees images.

Shared by `classify` (its `subject` rules) and `tags`: the same check, the same pool,
the same progress bar, and the first model error raised once the run is over.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.ai.describe import (
    CLASSIFY_QUESTION,
    DescribeDeps,
    describe_all,
)
from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.classify.ai.client import OllamaClient
    from media_hygiene.classify.ai.describe import DescribeOutcome, Question
    from media_hygiene.index.descriptions import DescriptionStore, PhotoVersion
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.subject_answers import Answering


@dataclass(frozen=True, slots=True)
class DescribeJob:
    """Who answers, where the answers go, progress and Ctrl+C, and what is asked."""

    client: OllamaClient
    store: DescriptionStore
    answering: Answering
    question: Question = CLASSIFY_QUESTION


def describe_checked(
    runtime: Runtime, photos: Sequence[PhotoVersion], job: DescribeJob
) -> DescribeOutcome:
    """Describe photos, after checking that the model sees images.

    Args:
        runtime: The model of `[classify.ai]` and the process pool.
        photos: The photos, in the order to describe them.
        job: The client, the cache, progress and Ctrl+C, the question.

    Returns:
        How it went.

    Raises:
        AiError: The model cannot be reached, or cannot see images.
    """
    model = runtime.settings.classify.ai.model
    asyncio.run(job.client.require_vision(model))
    progress = job.answering.progress
    with runtime.executor_factory() as executor:
        deps = DescribeDeps(
            job.client,
            job.store,
            executor,
            progress,
            job.answering.stopped,
            job.question,
        )
        progress.start(Step(_("Describing photos"), model), len(photos))
        try:
            outcome = asyncio.run(describe_all(photos, deps))
        finally:
            progress.stop()
    if outcome.errors:
        raise outcome.errors[0]
    return outcome
