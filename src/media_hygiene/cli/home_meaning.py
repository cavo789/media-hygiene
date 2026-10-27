"""Search by meaning as the home page builds it (0425): the model of `tags --meaning`.

The first half counts the photos without a vector; the second looks at them on this
computer's processor, each vector kept at once (a stop keeps them). Only the cache is
written: the photos stay read-only, and nothing about them is sent.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _, ngettext
from media_hygiene.index.repository import FactsRepository
from media_hygiene.meaning.clip import MODEL
from media_hygiene.meaning.embedder import ClipImages
from media_hygiene.meaning.files import clip_files
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.scan.progress import Step
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_tags_models import TagFigures, TagsRunner
from media_hygiene.services.meaning import MeaningWork, meaning_work, see_photos
from media_hygiene.services.subject_answers import Answering
from media_hygiene.services.tag_files import tag_files
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.console.page_progress import PageProgress
    from media_hygiene.services.runtime import Runtime


def page_meaning(source: Runtime | FreshRuntime) -> TagsRunner:
    """The two halves of search by meaning, on the settings and index of `home`.

    Args:
        source: Settings, mount points; read again at each half when fresh.

    Returns:
        The runner the page's `HomeTags` starts.
    """
    return TagsRunner(partial(_prepare, source), partial(_look, source))


def _runtime(source: Runtime | FreshRuntime) -> Runtime:
    """The runtime, with the settings the files hold now; meaning must be on.

    Args:
        source: The runtime, or where to read it.

    Returns:
        The runtime.

    Raises:
        MediaHygieneError: `[tags] meaning` is off.
    """
    runtime = source.runtime() if isinstance(source, FreshRuntime) else source
    if not runtime.settings.tags.meaning:
        raise MediaHygieneError(
            _("Search by meaning is off: set meaning = true under [tags] first.")
        )
    ensure_writable(runtime, MountKind.CACHE)
    return runtime


def _work(runtime: Runtime, repository: FactsRepository) -> MeaningWork:
    """The photos of the index without a vector.

    Args:
        runtime: Settings and mount points.
        repository: The open index.

    Returns:
        The work.
    """
    files = tag_files(runtime, repository.connection, ())
    return meaning_work(repository.connection, files)


def _prepare(source: Runtime | FreshRuntime, progress: PageProgress) -> TagFigures:
    """Count the photos without a vector.

    Args:
        source: The runtime, or where to read it.
        progress: Where the step reports.

    Returns:
        The figures the page asks with.
    """
    runtime = _runtime(source)
    progress.start(Step(_("Reading the index"), ""), None)
    with FactsRepository.open(runtime.index_file) as repository:
        work = _work(runtime, repository)
    return TagFigures(
        files=len(work.missing),
        to_describe=len(work.missing),
        seconds_per_photo=work.seconds_per_photo,
        model=MODEL,
    )


def _look(
    source: Runtime | FreshRuntime,
    progress: PageProgress,
    stopped: Callable[[], bool],
) -> tuple[str, ...]:
    """Give each photo without a vector its vector (the model downloaded once).

    Args:
        source: The runtime, or where to read it.
        progress: Where each photo is counted.
        stopped: Asked between two photos: Stop, or the time is up.

    Returns:
        The lines the page shows at the end.
    """
    runtime = _runtime(source)
    cache = runtime.locations.cache_dir
    with FactsRepository.open(runtime.index_file) as repository:
        work = _work(runtime, repository)
        model = ClipImages(clip_files(cache), runtime.settings.tags.meaning_threads)
        progress.start(
            Step(
                _("Looking at the photos"),
                _("what each photo shows, for search by meaning"),
            ),
            len(work.missing),
        )
        answering = Answering(True, progress, stopped)  # noqa: FBT003
        outcome = see_photos(repository.connection, (work, model), answering)
        progress.stop()
    left = len(work.missing) - outcome.seen - outcome.unreadable
    return (
        ngettext(
            "{count} photo can now be found by what it shows; {left} left.",
            "{count} photos can now be found by what they show; {left} left.",
            outcome.seen,
        ).format(count=outcome.seen, left=max(left, 0)),
    )
