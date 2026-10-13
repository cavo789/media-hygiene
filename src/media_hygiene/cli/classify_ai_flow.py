"""`classify` and the local model: the estimate, the confirmation, then the answers.

Nothing is sent without a `subject` rule or `--sample`. Above `confirm_above` photos
to describe, the user is asked first; a refusal (or no terminal) keeps the cache only.
Ctrl+C stops between two photos: what is described stays in the cache.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.cli.describe_consent import may_describe
from media_hygiene.console.progress import RichProgress
from media_hygiene.console.subject_view import (
    show_answered,
    show_not_described,
    show_plan,
    show_sample,
    show_work,
)
from media_hygiene.i18n import _
from media_hygiene.services.classify_sample import run_sample
from media_hygiene.services.classify_subjects import SubjectStep
from media_hygiene.services.interrupt import StopRequest
from media_hygiene.services.subject_answers import Answering
from media_hygiene.services.subject_plan import subject_rules

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.classify.ai.models import Subject
    from media_hygiene.services.classify_inputs import ClassifyInputs
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class SubjectRequest:
    """`--no-describe` and `--yes`."""

    describe: bool = True
    yes: bool = False


def ask_subjects(
    runtime: Runtime, inputs: ClassifyInputs, request: SubjectRequest
) -> Mapping[str, Mapping[Path, Subject]]:
    """Answer the `subject` rules, describing what the cache lacks when allowed.

    Args:
        runtime: Settings, cache, output.
        inputs: The files and the scope.
        request: `--no-describe` and `--yes`.

    Returns:
        The subjects of each rule; empty without a `subject` rule.
    """
    if not subject_rules(runtime.settings.classify):
        return {}
    output = runtime.output
    _tip_cache(runtime)
    with SubjectStep(runtime) as step:
        plan = step.plan(inputs)
        show_plan(output, plan)
        if request.describe:
            show_work(output, plan, runtime.settings.classify.ai.model)
        else:
            show_not_described(output, plan)
        describe = request.describe and may_describe(runtime, plan, request.yes)
        with StopRequest() as stop, RichProgress(output.console) as progress:
            answered = step.answer(plan, Answering(describe, progress, stop.requested))
    show_answered(output, answered)
    return answered.subjects


def sample_subjects(runtime: Runtime, inputs: ClassifyInputs, count: int) -> None:
    """`--sample N`: describe N random photos and print the cost of a full run.

    Args:
        runtime: Settings, cache, output.
        inputs: The files and the scope.
        count: How many photos.
    """
    output = runtime.output
    _tip_cache(runtime)
    with SubjectStep(runtime) as step:
        plan = step.plan(inputs)
        show_plan(output, plan)
        show_work(output, plan, runtime.settings.classify.ai.model)
        with StopRequest() as stop, RichProgress(output.console) as progress:
            result = run_sample(
                step,
                plan,
                (
                    count,
                    Answering(describe=True, progress=progress, stopped=stop.requested),
                ),
            )
    show_sample(output, result, runtime.mapper.to_host)


def _tip_cache(runtime: Runtime) -> None:
    """Warn that without /cache, every run describes the photos again.

    Args:
        runtime: Mount points and output.
    """
    if runtime.index_file is None:
        runtime.output.tip(
            _('Add -v "<a folder of yours>:/cache" to keep the descriptions.')
        )
