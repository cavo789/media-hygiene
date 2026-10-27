"""`tags` as the home page runs it: the same words, cache and model as `mh tags`.

The cheap half writes the folder, name, date and place words of every file of the
index and counts the photos the model would still describe; the model's half sends
them, then gives every photo the cached answers. Settings are read as the files hold
them when each half starts.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.scan.progress import Step
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_tags_models import TagFigures, TagsRunner
from media_hygiene.services.subject_answers import Answering
from media_hygiene.services.tag_describe import describe_photos
from media_hygiene.services.tags import TagStep
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.console.page_progress import PageProgress
    from media_hygiene.services.runtime import Runtime


def page_tags(source: Runtime | FreshRuntime) -> TagsRunner:
    """The two halves of `tags`, on the settings and index of `home`.

    Args:
        source: Settings, mount points; read again at each half when fresh.

    Returns:
        The runner the page's `HomeTags` starts.
    """
    return TagsRunner(partial(_prepare, source), partial(_describe, source))


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
    """Write the cheap words and the cached answers, count what is left.

    Args:
        source: The runtime, or where to read it.
        progress: Where each step reports.

    Returns:
        The figures the page asks with.

    Raises:
        MediaHygieneError: The index holds no photo nor video.
    """
    runtime = _runtime(source)
    with TagStep(runtime) as step:
        progress.start(Step(_("Reading the index"), ""), None)
        work = step.plan(())
        if not work.files:
            raise MediaHygieneError(
                _("No photo nor video in the cache: run the audit first.")
            )
        progress.start(Step(_("Words of folders, names, dates and places"), ""), None)
        step.cheap(work)
        step.derive(work)
        model = runtime.settings.classify.ai.model if step.vision_on else ""
    return TagFigures(
        files=len(work.files),
        to_describe=len(work.missing),
        seconds_per_photo=work.seconds_per_photo,
        model=model,
    )


def _describe(
    source: Runtime | FreshRuntime,
    progress: PageProgress,
    stopped: Callable[[], bool],
) -> tuple[str, ...]:
    """Describe what the cache lacks, then give every photo the cached answers.

    Args:
        source: The runtime, or where to read it.
        progress: Where each photo is counted.
        stopped: Asked between two photos: Stop, or the time is up.

    Returns:
        The lines the page shows at the end.
    """
    runtime = _runtime(source)
    with TagStep(runtime) as step:
        work = step.plan(())
        # The window of mh says why the PC works, and where to stop it (review of 0343).
        runtime.output.info(
            ngettext(
                "The home page has {count} photo described by the model: "
                "Stop is on the page.",
                "The home page has {count} photos described by the model: "
                "Stop is on the page.",
                len(work.missing),
            ).format(count=len(work.missing))
        )
        answering = Answering(True, progress, stopped)  # noqa: FBT003
        outcome = describe_photos(step, work, answering)
        tagged = step.derive(work)
    left = len(work.missing) - outcome.described
    return (
        ngettext(
            "{count} photo described; kept in the cache.",
            "{count} photos described; kept in the cache.",
            outcome.described,
        ).format(count=outcome.described),
        ngettext(
            "{count} photo has the words of the vision model; {left} left.",
            "{count} photos have the words of the vision model; {left} left.",
            tagged,
        ).format(count=tagged, left=max(left, 0)),
    )
