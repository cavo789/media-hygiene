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
from typing import TYPE_CHECKING

from rich.markup import escape

from media_hygiene.classify.ai.client import OllamaClient
from media_hygiene.classify.ai.landmark_prompt import landmark_request, read_landmark
from media_hygiene.errors import AiError
from media_hygiene.i18n import _
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.spot_picks import save_pick
from media_hygiene.report.thumbnails import jpeg_preview
from media_hygiene.scan.progress import Step
from media_hygiene.services.spot_scan import spot_index
from media_hygiene.services.spot_vision_work import landmark_work

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable, Sequence
    from concurrent.futures import Executor

    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.spot_vision_work import Work


@dataclass(slots=True)
class VisionPicks:
    """How the run went: photos asked about, a landmark picked, none, unclear."""

    asked: int = 0
    picked: int = 0
    none: int = 0
    unclear: int = 0  # undecodable, or an answer outside the list

    def said(self) -> str:
        """Say how the run went.

        Returns:
            One line, in the language in use.
        """
        return _(
            "🤖 {asked} photos shown to the model: {picked} landmarks picked, "
            "{none} showing none, {unclear} unclear (left as they were)."
        ).format(
            asked=self.asked,
            picked=self.picked,
            none=self.none,
            unclear=self.unclear,
        )


@dataclass(frozen=True, slots=True)
class _Asking:
    """What asking needs: the model, the index, the pool, the progress, Stop."""

    client: OllamaClient
    connection: sqlite3.Connection
    executor: Executor
    progress: ProgressSink
    stopped: Callable[[], bool]
    to_host: Callable[[Path], str]


def pick_landmarks(
    runtime: Runtime,
    progress: ProgressSink,
    stopped: Callable[[], bool] = lambda: False,
) -> VisionPicks:
    """Ask the model about each located photo not yet picked nor typed by hand.

    Args:
        runtime: Settings (`[classify.ai]`), the index, the process pool.
        progress: Where the progress line goes.
        stopped: Asked before each photo: the picks made so far stay (0641).

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
        work = landmark_work(runtime, repository.connection)
        if not work:
            return VisionPicks()
        client = OllamaClient(settings)
        asyncio.run(client.require_vision(settings.model))
        with runtime.executor_factory() as executor:
            asking = _Asking(
                client,
                repository.connection,
                executor,
                progress,
                stopped,
                runtime.mapper.to_host,
            )
            progress.start(
                Step(_("Picking the landmark each photo shows"), settings.model),
                len(work),
            )
            try:
                return asyncio.run(_ask_all(work, asking))
            finally:
                progress.stop()


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
        if asking.stopped():
            break
        asking.progress.current(asking.to_host(Path(photo.path)))
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
