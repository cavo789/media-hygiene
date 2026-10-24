"""Where `shrink --try` writes its drafts, and how they never stay (0307).

Only in `/cache/shrink-try/<run>/` (the cache volume): never next to the photos, never
in a folder Windows sees. The command removes its run's folder when the page closes,
whatever ends it; one left by a crash (`docker kill`, the PC off) is removed by the
next `shrink`, unless another `shrink --try` is running. That one holds a lock file it
touches every `_BEAT_SECONDS`: each run is its own container (its own PIDs), so a lock
is alive while it was touched less than `_STALE_SECONDS` ago, not while a PID exists.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import socket
import threading
import time
from typing import TYPE_CHECKING, Final, Self

if TYPE_CHECKING:
    from pathlib import Path

TRY_FOLDER: Final = "shrink-try"
_LOCK: Final = "try.lock"
_BEAT_SECONDS: Final = 10.0
_STALE_SECONDS: Final = 60.0
ROOM_FACTOR: Final = 2  # free space asked before a draft: twice its estimated size


def drafts_root(cache_dir: Path) -> Path:
    """The folder of every draft.

    Args:
        cache_dir: The cache mount point.

    Returns:
        `<cache>/shrink-try`.
    """
    return cache_dir / TRY_FOLDER


def held(root: Path) -> bool:
    """Tell whether a `shrink --try` is running on this cache.

    Args:
        root: The drafts folder.

    Returns:
        True while its lock was touched less than `_STALE_SECONDS` ago.
    """
    try:
        touched = (root / _LOCK).stat().st_mtime
    except OSError:
        return False
    return time.time() - touched < _STALE_SECONDS


def sweep(root: Path) -> int | None:
    """Remove what a previous run left, unless a `shrink --try` is running.

    Args:
        root: The drafts folder.

    Returns:
        The bytes removed (0 when nothing was left); None when another run holds it.
    """
    if not root.is_dir():
        return 0
    if held(root):
        return None
    removed = 0
    for entry in sorted(root.rglob("*"), reverse=True):
        with contextlib.suppress(OSError):
            if entry.is_dir():
                entry.rmdir()
                continue
            removed += entry.stat().st_size
            entry.unlink()
    return removed


def has_room(folder: Path, estimated: int) -> bool:
    """Tell whether the cache can take one more draft.

    Args:
        folder: Where the draft goes.
        estimated: Its estimated size, in bytes.

    Returns:
        True when the free space is at least `ROOM_FACTOR` times that.
    """
    try:
        free = shutil.disk_usage(folder).free
    except OSError:
        return False
    return free >= ROOM_FACTOR * estimated


class TryLock:
    """The lock of one `shrink --try`: taken, touched while it runs, then removed."""

    __slots__ = ("_file", "_stop", "_thread")

    def __init__(self, root: Path) -> None:
        """Prepare the lock of a drafts folder.

        Args:
            root: The drafts folder.
        """
        self._file = root / _LOCK
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._beat, daemon=True)

    def __enter__(self) -> Self:
        """Take the lock, then keep it alive.

        Returns:
            The lock.

        Raises:
            FileExistsError: Another `shrink --try` holds it.
        """
        root = self._file.parent
        root.mkdir(parents=True, exist_ok=True)
        if held(root):
            raise FileExistsError(self._file)
        self._file.unlink(missing_ok=True)  # a stale one: its run is gone
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        descriptor = os.open(self._file, flags, 0o644)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(f"{socket.gethostname()} {os.getpid()}\n")
        self._thread.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Stop touching the lock and remove it.

        Args:
            *exc_info: Exception details from the `with` statement (unused).
        """
        self._stop.set()
        self._thread.join()
        self._file.unlink(missing_ok=True)

    def _beat(self) -> None:
        """Touch the lock until the run ends."""
        while not self._stop.wait(_BEAT_SECONDS):
            with contextlib.suppress(OSError):
                os.utime(self._file)
