"""The `subject` rules: describe the samples missing from the cache, then map them.

Describing needs a vision model and time; mapping is text only, and cached too. The
answers become the subjects the rules read; what was not described stays to the
other rules.
"""

from __future__ import annotations

import asyncio
from contextlib import ExitStack
from typing import TYPE_CHECKING, Self

from media_hygiene.classify.ai.client import OllamaClient
from media_hygiene.classify.ai.describe import (
    DescribeDeps,
    DescribeOutcome,
    describe_all,
)
from media_hygiene.classify.ai.mapping import MapDeps
from media_hygiene.classify.ai.prompts import version
from media_hygiene.classify.ai.subjects import per_photo, subjects_of
from media_hygiene.i18n import _
from media_hygiene.index.descriptions import DescriptionStore
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.progress import Step
from media_hygiene.services.subject_answers import Answered, answers_of
from media_hygiene.services.subject_plan import plan_subjects

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.classify.ai.models import Subject
    from media_hygiene.config.classify_rules import ClassifyRule
    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.classify_inputs import ClassifyInputs
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.subject_answers import Answering
    from media_hygiene.services.subject_plan import SubjectPlan


class SubjectStep:
    """Asks the local model about the photos no stronger rule decided.

    A context manager: the index stays open for the whole step, so that an index in
    memory (no /cache mount) still holds what this run described.
    """

    def __init__(self, runtime: Runtime) -> None:
        """Prepare the step.

        Args:
            runtime: Settings, cache file, process pool.
        """
        self._runtime = runtime
        self._ai = runtime.settings.classify.ai
        self._client = OllamaClient(self._ai)
        self._stack = ExitStack()
        self._opened: DescriptionStore | None = None

    def __enter__(self) -> Self:
        """Open the index.

        Returns:
            The step.
        """
        repository = self._stack.enter_context(
            FactsRepository.open(self._runtime.index_file)
        )
        asked = (self._ai.model, version("describe"))
        self._opened = DescriptionStore(repository.connection, asked)
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Commit and close the index.

        Args:
            *exc_info: Exception details from the `with` statement (unused).
        """
        self._opened = None
        self._stack.close()

    def plan(self, inputs: ClassifyInputs) -> SubjectPlan:
        """Find the units, their samples and the samples to describe.

        Args:
            inputs: The files and the scope.

        Returns:
            The plan.
        """
        return plan_subjects(inputs, self._runtime.settings.classify, self.store)

    def answer(self, plan: SubjectPlan, answering: Answering) -> Answered:
        """Describe what is missing (when asked to), then map, rule by rule.

        Args:
            plan: The plan.
            answering: Describe or not, progress, Ctrl+C.

        Returns:
            The subjects of each rule.
        """
        outcome = DescribeOutcome()
        if answering.describe and plan.missing:
            outcome = self.describe(plan.missing, answering)
        deps = MapDeps(self._client, self.store, answering.progress)
        subjects = {rule.name: self._subjects(plan, rule, deps) for rule in plan.rules}
        return Answered(subjects, outcome)

    def describe(
        self, photos: Sequence[PhotoVersion], answering: Answering
    ) -> DescribeOutcome:
        """Describe photos, after checking that the model sees images.

        Args:
            photos: The photos.
            answering: Progress and Ctrl+C.

        Returns:
            How it went.

        Raises:
            AiError: The model cannot be reached, or cannot see images.
        """
        asyncio.run(self._client.require_vision(self._ai.model))
        progress = answering.progress
        with self._runtime.executor_factory() as executor:
            deps = DescribeDeps(
                self._client, self.store, executor, progress, answering.stopped
            )
            progress.start(Step(_("Describing photos"), self._ai.model), len(photos))
            try:
                outcome = asyncio.run(describe_all(photos, deps))
            finally:
                progress.stop()
        if outcome.errors:
            raise outcome.errors[0]
        return outcome

    def map(
        self, plan: SubjectPlan, rule: ClassifyRule, progress: ProgressSink
    ) -> dict[Path, str]:
        """Map the described samples to the categories of one rule.

        Args:
            plan: The plan: the samples and their versions.
            rule: The rule.
            progress: Where to show progress.

        Returns:
            The category of each described sample (empty: none fits).
        """
        return answers_of(plan, rule, MapDeps(self._client, self.store, progress))

    def _subjects(
        self, plan: SubjectPlan, rule: ClassifyRule, deps: MapDeps
    ) -> dict[Path, Subject]:
        """The subjects one rule gives.

        Args:
            plan: The plan.
            rule: The rule.
            deps: Model, cache, progress.

        Returns:
            The subject of each file its answers cover.
        """
        answers = answers_of(plan, rule, deps)
        assign = per_photo if rule.per_photo else subjects_of
        return assign(plan.units, plan.samples, answers)

    @property
    def store(self) -> DescriptionStore:
        """The descriptions of the configured model and prompt.

        Returns:
            The store.

        Raises:
            RuntimeError: The step is used outside its `with` block.
        """
        if self._opened is None:
            message = "SubjectStep used outside its with block"
            raise RuntimeError(message)
        return self._opened
