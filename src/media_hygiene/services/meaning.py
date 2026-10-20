"""`tags` and search by meaning: the vector of each photo the index lacks.

Opt-in (`[tags] meaning`, `tags --meaning`). The model runs here, on the CPU, one
photo at a time on `[tags] meaning_threads` threads (it holds 1.5 GB: one copy
only); each vector is committed at once, so Ctrl+C keeps what is done and the next
run goes on. Identical files (same digest) are looked at once. Photos and the
previews of RAW files only: a video has no vector.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.index.meaning_rows import MeaningStore
from media_hygiene.meaning.clip import MODEL, SECONDS_PER_PHOTO
from media_hygiene.report.thumbnails import unreadable_errors, upright_picture
from media_hygiene.scan.filters import media_kind
from media_hygiene.services.tag_work import version_of

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence

    import numpy as np
    from numpy.typing import NDArray

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.meaning.embedder import ImageReader
    from media_hygiene.services.subject_answers import Answering

_SEEN: Final = frozenset({MediaKind.IMAGE, MediaKind.RAW})
# Decoded at least this large (a JPEG at a reduced scale, by libjpeg), then brought
# to the 224 pixels the model reads: twice its side keeps the detail it sees.
_EDGE: Final = 448


@dataclass(frozen=True, slots=True)
class MeaningWork:
    """The photos of a run without a vector, and how long they should take."""

    missing: tuple[MediaInput, ...]
    seconds_per_photo: float

    @property
    def estimate(self) -> float:
        """How long looking at the missing photos should take.

        Returns:
            Seconds; identical files counted once.
        """
        digests = {file.digest or str(file.path) for file in self.missing}
        return len(digests) * self.seconds_per_photo


@dataclass(slots=True)
class MeaningOutcome:
    """How a run went: photos looked at, undecodable ones, Ctrl+C."""

    seconds: float = 0.0
    seen: int = 0
    unreadable: int = 0
    stopped: bool = False


def meaning_work(
    connection: sqlite3.Connection, files: Sequence[MediaInput]
) -> MeaningWork:
    """Find the photos of a run whose present version has no vector.

    Args:
        connection: The open index.
        files: The files of the run.

    Returns:
        The work, its time from this machine's own pace once known.
    """
    store = MeaningStore(connection, MODEL)
    photos = [file for file in files if media_kind(file.path) in _SEEN]
    missing = {photo.path for photo in store.missing(map(version_of, photos))}
    seconds = store.seconds_per_photo() or SECONDS_PER_PHOTO
    work = tuple(file for file in photos if file.path in missing)
    return MeaningWork(work, seconds)


def see_photos(
    connection: sqlite3.Connection,
    work: tuple[MeaningWork, ImageReader],
    answering: Answering,
) -> MeaningOutcome:
    """Give each missing photo its vector, until done or Ctrl+C.

    Args:
        connection: The open index, written.
        work: The photos, and the model.
        answering: Where to show progress, and whether to stop.

    Returns:
        How it went.
    """
    missing, model = work[0].missing, work[1]
    store = MeaningStore(connection, MODEL)
    outcome = MeaningOutcome()
    shared: dict[str, NDArray[np.float32]] = {}  # digest → vector, for copies
    for file in missing:
        if answering.stopped():
            outcome.stopped = True
            break
        answering.progress.advance()
        known = shared.get(file.digest or "")
        if known is not None:
            store.put(version_of(file), known, 0.0)  # a copy: no time of its own
            outcome.seen += 1
            continue
        started = time.monotonic()
        try:
            vector = model.image(upright_picture(file.path, _EDGE))
        except unreadable_errors():
            outcome.unreadable += 1
            continue
        seconds = time.monotonic() - started
        store.put(version_of(file), vector, seconds)
        if file.digest:
            shared[file.digest] = vector
        outcome.seconds += seconds
        outcome.seen += 1
    return outcome
