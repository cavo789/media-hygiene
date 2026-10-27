"""The face scan of `people` as the home page runs it (0424): the cache of `mh people`.

The first half counts the photos whose faces the cache lacks; the second analyses them,
each photo's faces committed at once (a stop keeps them), then groups every face. Only
the cache is written: the photos stay read-only.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MediaHygieneError
from media_hygiene.faces.models import FACE_MODEL
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.scan.progress import Step
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_tags_models import TagFigures, TagsRunner
from media_hygiene.services.people import PeopleStep
from media_hygiene.services.people_find import workers
from media_hygiene.services.subject_answers import Answering
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.console.page_progress import PageProgress
    from media_hygiene.services.runtime import Runtime

# Estimated from the detector's usual cost on a processor (0424), one worker: the page's
# first guess; `mh-measure.ps1` is where a real figure would come from.
_SECONDS_PER_PHOTO: Final = 0.35


def page_people(source: Runtime | FreshRuntime) -> TagsRunner:
    """The two halves of the face scan, on the settings and index of `home`.

    Args:
        source: Settings, mount points; read again at each half when fresh.

    Returns:
        The runner the page's `HomeTags` starts.
    """
    return TagsRunner(partial(_prepare, source), partial(_scan, source))


def _runtime(source: Runtime | FreshRuntime) -> Runtime:
    """The runtime, with the settings the files hold now.

    Args:
        source: The runtime, or where to read it.

    Returns:
        The runtime.
    """
    runtime = source.runtime() if isinstance(source, FreshRuntime) else source
    ensure_writable(runtime, MountKind.CACHE)
    return runtime


def _prepare(source: Runtime | FreshRuntime, progress: PageProgress) -> TagFigures:
    """Count the photos whose faces the cache lacks.

    Args:
        source: The runtime, or where to read it.
        progress: Where the step reports.

    Returns:
        The figures the page asks with.

    Raises:
        MediaHygieneError: The index holds no photo.
    """
    with PeopleStep(_runtime(source)) as step:
        progress.start(Step(_("Reading the index"), ""), None)
        work = step.plan(())
    if not work.photos:
        raise MediaHygieneError(_("No photo in the cache: run the audit first."))
    return TagFigures(
        files=len(work.photos),
        to_describe=len(work.missing),
        seconds_per_photo=_SECONDS_PER_PHOTO / workers(),
        model=FACE_MODEL,
    )


def _scan(
    source: Runtime | FreshRuntime,
    progress: PageProgress,
    stopped: Callable[[], bool],
) -> tuple[str, ...]:
    """Find the faces the cache lacks, then group every face.

    Args:
        source: The runtime, or where to read it.
        progress: Where each photo is counted.
        stopped: Asked between two photos: Stop, or the time is up.

    Returns:
        The lines the page shows at the end.
    """
    runtime = _runtime(source)
    with PeopleStep(runtime) as step:
        work = step.plan(())
        runtime.output.info(
            ngettext(
                "The home page has {count} photo scanned for faces: "
                "Stop is on the page.",
                "The home page has {count} photos scanned for faces: "
                "Stop is on the page.",
                len(work.missing),
            ).format(count=len(work.missing))
        )
        answering = Answering(True, progress, stopped)  # noqa: FBT003
        outcome = step.find(work.missing, answering)
        groups = len(step.result(work).groups.people)
    left = len(work.missing) - outcome.analysed - outcome.unreadable
    return (
        ngettext(
            "{count} photo scanned, {faces} faces found; kept in the cache.",
            "{count} photos scanned, {faces} faces found; kept in the cache.",
            outcome.analysed,
        ).format(count=outcome.analysed, faces=outcome.faces),
        ngettext(
            "{count} group of faces on the people page; {left} photos left.",
            "{count} groups of faces on the people page; {left} photos left.",
            groups,
        ).format(count=groups, left=max(left, 0)),
    )
