"""🤖 The landmark each photo shows, as the home page runs it (0641): `spots --vision`.

The first half fills the rows missing and lists the photos the model would be asked
about, some of them for the page to show; the second shows them to the local model,
each pick committed at once (a stop keeps them). Only the cache is written.
"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Final
from urllib.parse import urlencode

from media_hygiene.i18n import _
from media_hygiene.index.repository import FactsRepository
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.scan.progress import Step
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.search.folders import FOLDER_QUERY
from media_hygiene.search.views import JPEG, THUMB_PREFIX
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_tags_models import (
    AskedPhoto,
    TagFigures,
    TagsRunner,
)
from media_hygiene.services.spot_scan import scan_spots, spot_index
from media_hygiene.services.spot_vision import pick_landmarks
from media_hygiene.services.spot_vision_work import landmark_work
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from media_hygiene.console.page_progress import PageProgress
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.spot_vision_work import Work

# Enough to judge the run, spread over the list; the button states the whole count.
SHOWN: Final = 60


def page_spots(source: Runtime | FreshRuntime) -> TagsRunner:
    """The two halves of the vision pick, on the settings and index of `home`.

    Args:
        source: Settings, mount points; read again at each half when fresh.

    Returns:
        The runner the page's `HomeTags` starts.
    """
    return TagsRunner(partial(_prepare, source), partial(_ask, source))


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


def _shown(runtime: Runtime, work: Sequence[Work]) -> tuple[AskedPhoto, ...]:
    """Some of the photos asked about, evenly spread: what the page shows first.

    Args:
        runtime: Maps the paths to the user's.
        work: The photos and their candidates.

    Returns:
        At most `SHOWN`.
    """
    step = max(1, len(work) / SHOWN)
    chosen = (work[int(place * step)] for place in range(min(SHOWN, len(work))))
    to_host = runtime.mapper.to_host
    return tuple(
        AskedPhoto(
            thumb=f"{THUMB_PREFIX}{photo.key}{JPEG}",
            title=f"{to_host(Path(photo.path))}\n{', '.join(names)}",
            url=f"{SEARCH_PAGE_PATH}?"
            + urlencode({FOLDER_QUERY: to_host(Path(photo.path).parent)}),
        )
        for photo, names in chosen
    )


def _prepare(source: Runtime | FreshRuntime, progress: PageProgress) -> TagFigures:
    """Fill the rows missing, list the photos to ask about; nothing is sent.

    Args:
        source: The runtime, or where to read it.
        progress: Where each step reports.

    Returns:
        The figures and photos the page asks with.
    """
    runtime = _runtime(source)
    scan_spots(runtime, progress)
    progress.start(Step(_("Reading the index"), ""), None)
    with FactsRepository.open(spot_index(runtime)) as repository:
        work = landmark_work(runtime, repository.connection)
    ai = runtime.settings.classify.ai
    return TagFigures(
        files=len(work),
        to_describe=len(work),
        seconds_per_photo=ai.seconds_per_photo,
        model=ai.model,
        photos=_shown(runtime, work),
    )


def _ask(
    source: Runtime | FreshRuntime,
    progress: PageProgress,
    stopped: Callable[[], bool],
) -> tuple[str, ...]:
    """Show the photos to the local model.

    Args:
        source: The runtime, or where to read it.
        progress: Where each photo is counted.
        stopped: Asked before each photo: Stop, or the time is up.

    Returns:
        The line the page shows at the end.
    """
    return (pick_landmarks(_runtime(source), progress, stopped).said(),)
