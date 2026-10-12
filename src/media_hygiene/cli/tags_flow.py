"""`tags`, step by step: the cheap words, the estimate, the confirmation, the model.

Nothing is sent without a model in `[classify.ai]`. Above `confirm_above` photos to
describe, the user is asked first; a refusal (or no terminal) keeps the cache only.
Ctrl+C stops between two photos: what is described stays in the cache.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rich.markup import escape

from media_hygiene.cli.describe_consent import may_describe
from media_hygiene.console.progress import RichProgress
from media_hygiene.console.tags_view import (
    show_cheap,
    show_described,
    show_tag_sample,
    show_vision,
    show_work,
)
from media_hygiene.i18n import _
from media_hygiene.services.interrupt import StopRequest
from media_hygiene.services.subject_answers import Answering
from media_hygiene.services.tag_describe import describe_photos, run_tag_sample
from media_hygiene.services.tags import TagStep

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.tag_work import TagWork


@dataclass(frozen=True, slots=True)
class TagRequest:
    """`--path`, `--no-describe`, `--sample N` and `--yes`."""

    within: tuple[Path, ...] = ()
    describe: bool = True
    sample: int = 0
    yes: bool = False


def run_tags(runtime: Runtime, request: TagRequest) -> bool:
    """Tag the files of the index, describing what the cache lacks when allowed.

    Args:
        runtime: Settings, cache, output.
        request: The options.

    Returns:
        False when the index holds no file below the folders asked for.
    """
    output = runtime.output
    model = runtime.settings.classify.ai.model
    with TagStep(runtime) as step:
        work = step.plan(request.within)
        if not work.files:
            output.warning(_("No photo nor video of the index below these folders."))
            return False
        show_cheap(output, work, step.cheap(work))
        if not step.vision_on:
            output.tip(
                escape(
                    _(
                        "Set [classify.ai] model to a local vision model (Ollama) to "
                        "add what the photos show: they are sent to its url, and only "
                        "there."
                    )
                )
            )
            return True
        show_work(output, work, model)
        if request.sample:
            _sample(step, work, request.sample)
        elif request.describe and may_describe(runtime, work, request.yes):
            with StopRequest() as stop, RichProgress(output.console) as progress:
                answering = Answering(True, progress, stop.requested)  # noqa: FBT003
                show_described(output, describe_photos(step, work, answering))
        show_vision(output, work, step.derive(work))
    return True


def _sample(step: TagStep, work: TagWork, count: int) -> None:
    """`--sample N`: describe N random photos and print the cost of a full run.

    Args:
        step: The open tag step: output and host paths.
        work: The work of a full run.
        count: How many photos.
    """
    runtime = step.runtime
    output = runtime.output
    with StopRequest() as stop, RichProgress(output.console) as progress:
        answering = Answering(True, progress, stop.requested)  # noqa: FBT003
        sample = run_tag_sample(step, work, (count, answering))
    show_tag_sample(output, sample, runtime.mapper.to_host)
