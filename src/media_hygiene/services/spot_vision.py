"""🤖 `spots --vision`: a local model picks the landmark each photo shows (0589).

The GPS alone names the nearest monument within `NEAR_M`: a cathedral photographed
from 400 m gets nothing, a photo taken next to a castle, facing away, gets the castle.
Here the local vision model of `[classify.ai]` sees the photo and picks among the
landmarks within `PICK_M` (a short list, never a free guess), or none. Offline: the
photo goes to the user's own model only. Each pick is committed at once, with its
source; a name typed by hand is never asked about nor replaced.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from rich.markup import escape

from media_hygiene.classify.ai.client import OllamaClient
from media_hygiene.classify.ai.landmark_prompt import landmark_request, read_landmark
from media_hygiene.errors import AiError, GeoDataError
from media_hygiene.geo.distance import Point
from media_hygiene.geo.landmarks import near_cells, shared_landmarks
from media_hygiene.i18n import _
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.spot_picks import Unpicked, save_pick, unpicked
from media_hygiene.report.thumbnails import jpeg_preview
from media_hygiene.scan.progress import Step
from media_hygiene.services.spot_scan import spot_index

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence
    from concurrent.futures import Executor

    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime

# How far a landmark a photo shows may lie: a cathedral seen from across a town.
PICK_M: Final = 1000.0
# The nearest ones only: a long list slows the model and invites a wrong pick.
MAX_CANDIDATES: Final = 10

type Work = tuple[Unpicked, tuple[str, ...]]


@dataclass(slots=True)
class VisionPicks:
    """How the run went: photos asked about, a landmark picked, none, unclear."""

    asked: int = 0
    picked: int = 0
    none: int = 0
    unclear: int = 0  # undecodable, or an answer outside the list


@dataclass(frozen=True, slots=True)
class _Asking:
    """What asking needs: the model, the index, the pool, the progress."""

    client: OllamaClient
    connection: sqlite3.Connection
    executor: Executor
    progress: ProgressSink


def pick_landmarks(runtime: Runtime, progress: ProgressSink) -> VisionPicks:
    """Ask the model about each located photo not yet picked nor typed by hand.

    Args:
        runtime: Settings (`[classify.ai]`), the index, the process pool.
        progress: Where the progress line goes.

    Returns:
        What was asked and answered; each pick is already in the index.

    Raises:
        AiError: No model is set, or it cannot be reached or cannot see images.
        MountError: The cache holds no index yet.
    """
    settings = runtime.settings.classify.ai
    if not settings.model:
        raise AiError(
            _("No local vision model is set: no photo was sent, nothing changed."),
            escape(_("Set [classify.ai] model to a local vision model (Ollama).")),
        )
    index = spot_index(runtime)
    with FactsRepository.open(index) as repository:
        work = _work(unpicked(repository.connection))
        if not work:
            return VisionPicks()
        client = OllamaClient(settings)
        asyncio.run(client.require_vision(settings.model))
        with runtime.executor_factory() as executor:
            asking = _Asking(client, repository.connection, executor, progress)
            progress.start(
                Step(_("Picking the landmark each photo shows"), settings.model),
                len(work),
            )
            try:
                return asyncio.run(_ask_all(work, asking))
            finally:
                progress.stop()


def _work(photos: Sequence[Unpicked]) -> list[Work]:
    """The photos with at least one landmark around, and those landmarks.

    Args:
        photos: The photos not picked yet.

    Returns:
        Each photo and its candidates, nearest first.
    """
    if not photos:
        return []
    points = [Point(photo.latitude, photo.longitude) for photo in photos]
    try:
        landmarks = shared_landmarks(near_cells(points))
    except GeoDataError:
        return []
    found = (
        (photo, landmarks.around(point, PICK_M)[:MAX_CANDIDATES])
        for photo, point in zip(photos, points, strict=True)
    )
    return [(photo, names) for photo, names in found if names]


async def _ask_all(work: Sequence[Work], asking: _Asking) -> VisionPicks:
    """Ask about each photo in turn, committing each pick.

    Args:
        work: The photos and their candidates.
        asking: Model, index, pool, progress.

    Returns:
        How it went.
    """
    outcome = VisionPicks()
    loop = asyncio.get_running_loop()
    model = asking.client.settings.model
    edge = asking.client.settings.image_edge
    for photo, names in work:
        asking.progress.current(photo.path)
        image = await loop.run_in_executor(
            asking.executor, jpeg_preview, Path(photo.path), edge
        )
        picked = None
        if image is not None:
            answer = await asking.client.chat(landmark_request(model, image, names))
            picked = read_landmark(answer, names)
        outcome.asked += 1
        if picked is None:
            outcome.unclear += 1
        else:
            save_pick(asking.connection, photo, picked)
            outcome.picked += bool(picked)
            outcome.none += not picked
        asking.progress.advance()
    return outcome
