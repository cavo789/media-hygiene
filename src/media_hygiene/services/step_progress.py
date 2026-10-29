"""The progress of a step that writes, shared with the home page (0361).

A step `mh` runs in its window while the home server stays up (0355) writes how far it
is into `.mh-step-progress.json` of the reports folder: done, total, the current file,
at most every half second (and once at the end). The server only reads it
(`GET /api/step`): it never has the photos read-write, the step runs in a container
of its own. Written beside, then renamed: the server never reads half a file.
"""

from __future__ import annotations

import json
import os
import time
from contextlib import suppress
from typing import TYPE_CHECKING, Final

from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.scan.progress import ProgressSink, Step

PROGRESS_FILE: Final = ".mh-step-progress.json"
EVERY_SECONDS: Final = 0.5  # at most two writes a second: a cheap read for the page
_WATCHING: Final = "3"  # `MEDIA_HYGIENE_LAUNCHER_STEPS` of an `mh` keeping the server


class SharedProgress:
    """A progress sink that also writes its progress for the home page."""

    def __init__(self, inner: ProgressSink, folder: Path) -> None:
        """Wrap a sink.

        Args:
            inner: The sink shown in the window (Rich).
            folder: The reports folder.
        """
        self._inner = inner
        self._file = folder / PROGRESS_FILE
        self._said: dict[str, object] = {"done": 0, "total": None, "current": ""}
        self._last = 0.0

    def start(self, step: Step, total: int | None) -> None:
        """Begin a step.

        Args:
            step: Its title and explanation.
            total: The units of work, None when unknown.
        """
        self._inner.start(step, total)
        self._said = {"title": step.title, "done": 0, "total": total, "current": ""}
        self._write(force=True)

    def advance(self, weight: int = 1) -> None:
        """Mark one unit of work as done.

        Args:
            weight: Its share of the step's weight.
        """
        self._inner.advance(weight)
        self._said["done"] = int(str(self._said["done"])) + 1
        self._write(force=False)

    def current(self, text: str) -> None:
        """Say which file is being worked on.

        Args:
            text: The file or action.
        """
        self._inner.current(text)
        self._said["current"] = text
        self._write(force=False)

    def stop(self) -> None:
        """End the step: its last state is written whatever the time."""
        self._inner.stop()
        self._write(force=True)

    def _write(self, *, force: bool) -> None:
        """Write the progress, at most every `EVERY_SECONDS` unless forced.

        Args:
            force: Write now (start, end).
        """
        now = time.monotonic()
        if not force and now - self._last < EVERY_SECONDS:
            return
        self._last = now
        beside = self._file.with_name(self._file.name + ".tmp")
        with suppress(OSError):  # the page loses a beat, the step goes on
            beside.write_text(json.dumps(self._said, ensure_ascii=False), "utf-8")
            beside.replace(self._file)


def shared(inner: ProgressSink, folder: Path) -> ProgressSink:
    """The sink a writing step uses: shared with the page when `mh` keeps the server.

    Args:
        inner: The sink shown in the window.
        folder: The reports folder.

    Returns:
        A `SharedProgress` under an `mh` that watches, else `inner` as is.
    """
    if os.environ.get(LAUNCHER_STEPS_VARIABLE) != _WATCHING:
        return inner
    with suppress(OSError):  # a new step: the last one's progress is not this one's
        (folder / PROGRESS_FILE).unlink(missing_ok=True)
    return SharedProgress(inner, folder)


def read_progress(folder: Path) -> dict[str, object] | None:
    """Read the progress of the step running, for `GET /api/step`.

    Args:
        folder: The reports folder.

    Returns:
        What it wrote, or None when there is none (or it cannot be read).
    """
    try:
        said = json.loads((folder / PROGRESS_FILE).read_text("utf-8"))
    except OSError, ValueError:
        return None
    return said if isinstance(said, dict) else None
