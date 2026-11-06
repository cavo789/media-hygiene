"""The progress of a step that writes, shared with the home page (0361).

A step `mh` runs in its window while the home server stays up (0355) writes how far it
is into `.mh-step-progress.json` of the reports folder: done, total, the current file,
at most every half second (and once at the end), and again every few seconds with the
time (`at`), a pulse: one long video writes nothing else for minutes, and a window of
`mh` closed stops it (0632). The server only reads it (`GET /api/step`): it never has
the photos read-write, the step runs in a container of its own. Written beside, then
renamed: the server never reads half a file.
"""

from __future__ import annotations

import json
import os
import threading
import time
from contextlib import suppress
from typing import TYPE_CHECKING, Final

from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.scan.progress import ProgressSink, Step

PROGRESS_FILE: Final = ".mh-step-progress.json"
EVERY_SECONDS: Final = 0.5  # at most two writes a second: a cheap read for the page
BEAT_SECONDS: Final = 5.0  # the pulse, whatever the step is doing
LOST_AFTER_SECONDS: Final = 60.0  # no pulse for this long: the step is not running
AT_KEY: Final = "at"
# Written by `mh` around the step it runs (`step_watch.WATCH.running`): the step's own
# container has not the variable below, only the server's has.
RUNNING_FILE: Final = ".mh-step-running.json"
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
        self._writing = threading.Lock()
        self._ended = threading.Event()
        self._pulse: threading.Thread | None = None

    def start(self, step: Step, total: int | None) -> None:
        """Begin a step.

        Args:
            step: Its title and explanation.
            total: The units of work, None when unknown.
        """
        self._inner.start(step, total)
        self._said = {"title": step.title, "done": 0, "total": total, "current": ""}
        self._write(force=True)
        self._ended.clear()
        if self._pulse is None:
            self._pulse = threading.Thread(target=self._beat, daemon=True)
            self._pulse.start()

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
        self._ended.set()
        if self._pulse is not None:
            self._pulse.join()
            self._pulse = None
        self._write(force=True)

    def _beat(self) -> None:
        """Write the time every few seconds until the step ends."""
        while not self._ended.wait(BEAT_SECONDS):
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
        said = self._said | {AT_KEY: time.time()}
        with (
            self._writing,
            suppress(OSError),
        ):  # the page loses a beat, the step goes on
            beside.write_text(json.dumps(said, ensure_ascii=False), "utf-8")
            beside.replace(self._file)


def shared(inner: ProgressSink, folder: Path) -> ProgressSink:
    """The sink a writing step uses: shared with the page when `mh` keeps the server.

    Args:
        inner: The sink shown in the window.
        folder: The reports folder.

    Returns:
        A `SharedProgress` under an `mh` that watches or runs this step beside its
        server, else `inner` as is.
    """
    watching = os.environ.get(LAUNCHER_STEPS_VARIABLE) == _WATCHING
    if not watching and not (folder / RUNNING_FILE).exists():
        return inner
    forget_progress(folder)  # a new step: the last one's progress is not this one's
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
    if not isinstance(said, dict):
        return None
    said.pop(AT_KEY, None)  # the pulse: `step_lost` reads it
    return said


def step_lost(folder: Path) -> bool:
    """Tell whether the step that wrote its progress stopped pulsing (0632).

    `at` comes from the step's container and is compared here, in the server's: both
    read the same clock, unlike the file's date, set by the host's disk.

    Args:
        folder: The reports folder.

    Returns:
        True when its last pulse is too old; False without a pulse to judge by.
    """
    try:
        at = json.loads((folder / PROGRESS_FILE).read_text("utf-8")).get(AT_KEY)
    except OSError, ValueError, AttributeError:
        return False
    if not isinstance(at, int | float):
        return False
    return time.time() - at > LOST_AFTER_SECONDS


def forget_progress(folder: Path) -> None:
    """Drop the progress of the last step: the next one is judged on its own.

    Args:
        folder: The reports folder.
    """
    with suppress(OSError):
        (folder / PROGRESS_FILE).unlink(missing_ok=True)
