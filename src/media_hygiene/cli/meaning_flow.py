"""`tags` and search by meaning: say the work, download the model once, look.

Opt-in: `[tags] meaning = true` or `tags --meaning`. The model runs on this computer's
processor, never a GPU, and nothing about the photos is sent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.meaning_view import (
    show_meaning_done,
    show_meaning_download,
    show_meaning_work,
)
from media_hygiene.console.progress import RichProgress
from media_hygiene.i18n import _
from media_hygiene.index.repository import FactsRepository
from media_hygiene.meaning.embedder import ClipImages
from media_hygiene.meaning.files import clip_files, clip_present
from media_hygiene.scan.progress import Step
from media_hygiene.services.interrupt import StopRequest
from media_hygiene.services.meaning import meaning_work, see_photos
from media_hygiene.services.subject_answers import Answering

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.services.runtime import Runtime


def run_meaning(runtime: Runtime, files: Sequence[MediaInput]) -> None:
    """Give the photos of a `tags` run their vectors, the missing ones only.

    Args:
        runtime: Settings, cache and output.
        files: The files of the run.
    """
    output = runtime.output
    cache = runtime.locations.cache_dir
    with FactsRepository.open(runtime.index_file) as repository:
        work = meaning_work(repository.connection, files)
        show_meaning_work(output, work)
        if not work.missing:
            return
        if not clip_present(cache):
            show_meaning_download(output)
        model = ClipImages(clip_files(cache), runtime.settings.tags.meaning_threads)
        step = Step(
            _("Looking at the photos"),
            _("what each photo shows, for search by meaning"),
        )
        with StopRequest() as stop, RichProgress(output.console) as progress:
            progress.start(step, len(work.missing))
            answering = Answering(True, progress, stop.requested)  # noqa: FBT003
            outcome = see_photos(repository.connection, (work, model), answering)
            progress.stop()
    show_meaning_done(output, outcome)
