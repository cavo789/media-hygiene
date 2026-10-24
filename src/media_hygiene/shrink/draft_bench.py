"""The drafts of `shrink --try`, encoded one at a time in the background (0307).

The same encoding as `--apply` (`ffmpeg_command` with its `Recipe`), proven the same
way (`check.flaw`), into `<run>/<n>.mp4`; then a frame of the original and one of the
draft at each of `INSTANTS` of its length (`<n>-a-<k>.jpg`, `<n>-b-<k>.jpg`): the
originals of old cameras play in no browser. The page shows each draft as it lands.
Before each one, the cache must have `ROOM_FACTOR` times its estimated size free, or
the drafts stop there. `stop()` kills the encoding under way.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.shrink.check import flaw
from media_hygiene.shrink.drafts import has_room
from media_hygiene.shrink.encode import ffmpeg_command
from media_hygiene.shrink.stoppable import STOPPED, run_stoppable

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.shrink import Recipe
    from media_hygiene.shrink.candidates import Candidate

INSTANTS: Final = (0.1, 0.5, 0.9)  # the shares of its length a frame is taken at
_SLOWER_THAN_FILM: Final = 10  # as `encode`: ten times the film, at least
_LEAST_SECONDS: Final = 600
_FRAME_SECONDS: Final = 60
_FRAME: Final = ("-frames:v", "1", "-q:v", "2", "-f", "image2")


class DraftState(StrEnum):
    """Where a draft stands."""

    WAITING = "waiting"
    ENCODING = "encoding"
    READY = "ready"
    FAILED = "failed"
    NO_ROOM = "no_room"


@dataclass(frozen=True, slots=True)
class Draft:
    """One video of the try, and its draft once encoded."""

    number: int
    video: Candidate
    state: DraftState = DraftState.WAITING
    size: int = 0  # bytes of the draft
    seconds: float = 0.0  # the encoding's time
    reason: str = ""  # why it failed


def draft_file(folder: Path, number: int) -> Path:
    """The draft of a video.

    Args:
        folder: The run's folder.
        number: The video's number in the try.

    Returns:
        `<folder>/<number>.mp4`.
    """
    return folder / f"{number}.mp4"


def frame_file(folder: Path, number: int, frame: tuple[str, int]) -> Path:
    """A frame of the original (`a`) or of the draft (`b`).

    Args:
        folder: The run's folder.
        number: The video's number in the try.
        frame: The side, `a` or `b`, and the instant's index in `INSTANTS`.

    Returns:
        `<folder>/<number>-<side>-<index>.jpg`.
    """
    side, index = frame
    return folder / f"{number}-{side}-{index}.jpg"


class DraftBench:
    """Encodes the drafts in a thread; the page reads them as they land."""

    def __init__(
        self, folder: Path, videos: tuple[Candidate, ...], recipe: Recipe
    ) -> None:
        """Prepare the drafts of a run.

        Args:
            folder: The run's folder, in the cache.
            videos: The videos to try, in the list's order.
            recipe: The encoding of `--apply`, and its tools.
        """
        self.folder = folder
        self._recipe = recipe
        self._drafts = [Draft(n, video) for n, video in enumerate(videos, 1)]
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._work, daemon=True)

    def start(self) -> None:
        """Start encoding, the first video first."""
        self._thread.start()

    def stop(self) -> None:
        """Stop now, the encoding under way killed, and wait for the thread."""
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join()

    def drafts(self) -> tuple[Draft, ...]:
        """Every draft as it stands now.

        Returns:
            Them, in the try's order.
        """
        with self._lock:
            return tuple(self._drafts)

    def _set(self, draft: Draft) -> None:
        """Record where a draft stands.

        Args:
            draft: Its new state.
        """
        with self._lock:
            self._drafts[draft.number - 1] = draft

    def _work(self) -> None:
        """Encode each draft in turn until the end, a stop, or no room left."""
        for draft in self.drafts():
            if self._stop.is_set():
                return
            if not has_room(self.folder, draft.video.estimated):
                for left in self.drafts()[draft.number - 1 :]:
                    self._set(replace(left, state=DraftState.NO_ROOM))
                return
            self._set(replace(draft, state=DraftState.ENCODING))
            started = time.monotonic()
            reason = self._encode(draft)
            if reason == STOPPED:
                return
            seconds = time.monotonic() - started
            target = draft_file(self.folder, draft.number)
            if reason is None:
                size = target.stat().st_size
                done = replace(draft, state=DraftState.READY, size=size)
            else:
                target.unlink(missing_ok=True)
                done = replace(draft, state=DraftState.FAILED, reason=reason)
            self._set(replace(done, seconds=seconds))

    def _encode(self, draft: Draft) -> str | None:
        """Encode one draft, prove it, then take its frames and the original's.

        Args:
            draft: The video.

        Returns:
            None when it worked, `STOPPED`, or why it failed.
        """
        recipe = self._recipe
        source, target = draft.video.path, draft_file(self.folder, draft.number)
        command = ffmpeg_command(recipe.tools.ffmpeg, (source, target), recipe.encoding)
        reason = run_stoppable(
            command,
            self._stop,
            max(_LEAST_SECONDS, draft.video.duration * _SLOWER_THAN_FILM),
        )
        if reason is not None:
            return reason
        lost = flaw((source, target), recipe.tools)
        if lost is not None:
            return lost
        for index, share in enumerate(INSTANTS):
            at = f"{draft.video.duration * share:.3f}"
            for side, video in (("a", source), ("b", target)):
                frame = frame_file(self.folder, draft.number, (side, index))
                command = (recipe.tools.ffmpeg, "-nostdin", "-v", "error", "-y")
                command = (*command, "-ss", at, "-i", str(video), *_FRAME, str(frame))
                said = run_stoppable(command, self._stop, _FRAME_SECONDS)
                if said is not None:
                    return (
                        said
                        if said == STOPPED
                        else _("no frame: {error}").format(error=said)
                    )
        return None
