"""`people`, step by step: forget, or find what the cache lacks, then group.

Ctrl+C stops between two photos: the faces found stay in the cache. `--sample N`
analyses N random photos and tells what a full run would take; `--forget` deletes every
face and shows that none is left, read back from the index.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.console.people_view import (
    show_absent,
    show_estimate,
    show_found,
    show_groups,
    show_missing,
    show_privacy,
)
from media_hygiene.console.progress import RichProgress
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.interrupt import StopRequest
from media_hygiene.services.people import PeopleStep
from media_hygiene.services.subject_answers import Answering

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.services.people_find import FindOutcome
    from media_hygiene.services.people_groups import PeopleGroups
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class PeopleRequest:
    """`--path`, `--sample N` and `--forget`."""

    within: tuple[Path, ...] = ()
    sample: int = 0
    forget: bool = False


def run_people(runtime: Runtime, request: PeopleRequest) -> PeopleGroups | None:
    """Find the faces the cache lacks, then group every face.

    Args:
        runtime: Settings, cache, output.
        request: The options.

    Returns:
        The groups; None after `--forget`, `--sample`, or without any photo.
    """
    output = runtime.output
    with PeopleStep(runtime) as step:
        if request.forget:
            _forget(runtime, step)
            return None
        work = step.plan(request.within)
        show_absent(output, work.absent)
        if not work.photos:
            output.warning(_("No photo of the index below these folders."))
            return None
        show_privacy(output)
        if request.sample:
            outcome = _find(runtime, step, step.sample(work, request.sample))
            left = len(work.missing) - outcome.analysed
            show_estimate(output, left, outcome.estimate(left))
            return None
        show_missing(output, len(work.missing), len(work.photos))
        if work.missing:
            _find(runtime, step, work.missing)
        groups = step.groups()
        show_groups(output, groups, (step.tally(), runtime.settings.people))
    return groups


def _find(
    runtime: Runtime, step: PeopleStep, photos: Sequence[PhotoVersion]
) -> FindOutcome:
    """Analyse photos with a progress bar, Ctrl+C stopping between two.

    Args:
        runtime: Output.
        step: The open step.
        photos: The photos.

    Returns:
        How it went, once said.
    """
    output = runtime.output
    with StopRequest() as stop, RichProgress(output.console) as progress:
        answering = Answering(True, progress, stop.requested)  # noqa: FBT003
        outcome = step.find(photos, answering)
    show_found(output, outcome)
    return outcome


def _forget(runtime: Runtime, step: PeopleStep) -> None:
    """Delete every face, then show what the index holds now.

    Args:
        runtime: Output.
        step: The open step.
    """
    output = runtime.output
    forgotten, left = step.store.forget()
    output.success(
        ngettext(
            "{count} face forgotten.",
            "{count} faces forgotten.",
            forgotten,
        ).format(count=human_number(forgotten))
    )
    output.info(
        _("Read back from the index: {faces} faces left.").format(
            faces=human_number(left)
        )
    )
