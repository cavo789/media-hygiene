"""`audit --people`: once the audit is done, find the faces, if the user agrees.

The photos the audit just listed are counted exactly; a few of them are analysed to
measure this computer's pace (kept, nothing is wasted), then the question is asked.
`--yes` skips it; without a terminal nothing waits for an answer: the audit ends without
faces. The face models are downloaded after the yes only, so the pace is measured
when they are already in the cache, and estimated otherwise.
"""

from __future__ import annotations

import sys
import time
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.next_steps import carried, suggest
from media_hygiene.cli.people_flow import find_shown
from media_hygiene.cli.review_options import PAGE_PORT
from media_hygiene.console.formatting import human_duration, human_number
from media_hygiene.console.people_view import show_groups, show_named, show_privacy
from media_hygiene.console.progress import RichProgress
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.next_command import NextVerb
from media_hygiene.services.people import PeopleStep
from media_hygiene.services.people_find import workers
from media_hygiene.services.people_models import models_present
from media_hygiene.services.subject_answers import Answering

if TYPE_CHECKING:
    from media_hygiene.services.people import PeopleWork
    from media_hygiene.services.runtime import Runtime

SAMPLE: Final = 10  # photos measured before asking
SAMPLE_SECONDS: Final = 5.0  # at most
# Seconds per photo and worker, decoding included, measured on the maintainer's PC
# (TODO 0089): the estimate before the models are in the cache.
TYPICAL_SECONDS: Final = 0.2


def audit_people(runtime: Runtime, yes: bool) -> None:  # noqa: FBT001
    """Count, measure, ask, then find the faces of the photos of the audit.

    Args:
        runtime: Settings, mount points and output.
        yes: `--yes`: no question.
    """
    output = runtime.output
    output.blank()
    if not runtime.persistent(MountKind.CACHE):
        output.warning(
            _("--people keeps the faces in the cache: mount /cache to look for them.")
        )
        return
    within = runtime.mounts.data_roots(runtime.locations.data_dir)
    with PeopleStep(runtime) as step:
        work = step.plan(within)
        if not work.missing:
            output.info(_("Faces: every photo of the audit was looked at already."))
            return
        show_privacy(output)
        line = _estimate(runtime, step, work)
        work = step.plan(within)
        if work.missing:
            output.info(line)
            if not _agreed(runtime, yes):
                return
            find_shown(runtime, step, work.missing)
        result = step.result(work)
        show_groups(output, result.groups, (result.tally, runtime.settings.people))
        show_named(output, result.named)
    output.info(_("Run 'people' to see the groups in your browser and name them."))
    if result.groups.people:
        # The audit's own step (copies to clean, bursts to review) comes after and wins.
        suggest(
            runtime,
            _("name the groups of faces in your browser, with 'people'."),
            NextVerb(carried(runtime, "people"), port=PAGE_PORT),
        )


def _estimate(runtime: Runtime, step: PeopleStep, work: PeopleWork) -> str:
    """Measure a few photos when the models are here, and say what the rest takes.

    Args:
        runtime: Mount points and output.
        step: The open step.
        work: The photos of the audit.

    Returns:
        The line saying the count left and the estimate.
    """
    left = len(work.missing)
    if models_present(runtime):
        deadline = time.monotonic() + SAMPLE_SECONDS
        with RichProgress(runtime.output.console) as progress:
            stopped = partial(_late, deadline)
            answering = Answering(describe=True, progress=progress, stopped=stopped)
            outcome = step.find(step.sample(work, SAMPLE), answering)
        left -= outcome.analysed
        if outcome.analysed:
            return ngettext(
                "{count} photo has not been looked at for faces yet: about "
                "{duration} on this PC (measured on {measured} photos).",
                "{count} photos have not been looked at for faces yet: about "
                "{duration} on this PC (measured on {measured} photos).",
                left,
            ).format(
                count=human_number(left),
                duration=human_duration(outcome.estimate(left)),
                measured=outcome.analysed,
            )
    pace = step.store.tally().seconds_per_photo or TYPICAL_SECONDS
    return ngettext(
        "{count} photo has not been looked at for faces yet: about {duration} "
        "(estimated; the two face models, 39 MB, are downloaded first).",
        "{count} photos have not been looked at for faces yet: about {duration} "
        "(estimated; the two face models, 39 MB, are downloaded first).",
        left,
    ).format(count=human_number(left), duration=human_duration(pace * left / workers()))


def _late(deadline: float) -> bool:
    """Tell whether the measure has taken long enough.

    Args:
        deadline: `time.monotonic()` at which it stops.

    Returns:
        True once passed.
    """
    return time.monotonic() > deadline


def has_terminal() -> bool:
    """Tell whether someone can answer a question.

    Returns:
        True when the standard input is a terminal.
    """
    return sys.stdin.isatty()


def _agreed(runtime: Runtime, yes: bool) -> bool:  # noqa: FBT001
    """Ask whether to look for the faces now; never wait without a terminal.

    Args:
        runtime: Output.
        yes: `--yes`.

    Returns:
        True to go on.
    """
    output = runtime.output
    output.info(
        _(
            "Ctrl+C stops between two photos: the faces found are kept, and the next "
            "run goes on."
        )
    )
    if yes:
        return True
    if not has_terminal():
        output.warning(
            _(
                "No terminal to answer in: the audit ends without faces. Add --yes "
                "to look for them without a question."
            )
        )
        return False
    if output.confirm(_("The audit is done; look for the faces now?")):
        return True
    output.info(
        _("No face looked for: 'people', or the next 'audit --people', does it later.")
    )
    return False
