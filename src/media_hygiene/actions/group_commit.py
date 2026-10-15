"""Journal lines made durable together: one `fsync` for every line written meanwhile.

A `pending` line must be on the disk before its action: its writer waits for an
`fsync` that started after the line was written. While one `fsync` runs (a few ms,
more on a shared folder), the other workers write their own lines; the next `fsync`
covers all of them at once (group commit). A `done` line waits for nothing: the next
`fsync`, or the one made when the journal closes, carries it. Lost in a power cut, it
leaves its action `pending`, which `undo` and a resumed `sort` already judge by what
is on the disk.
"""

from __future__ import annotations

import os
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TextIO


class GroupCommit:
    """Appends lines to a stream, and syncs every line written up to a given one."""

    def __init__(self, stream: TextIO) -> None:
        """Wrap an append-mode text stream.

        Args:
            stream: The journal, opened for appending.
        """
        self._stream = stream
        self._write_lock = threading.Lock()
        self._sync_lock = threading.Lock()
        self._written = 0  # lines handed to the system
        self._synced = 0  # lines known to be on the disk
        self.syncs = 0  # `fsync` calls made

    def append(self, line: str) -> int:
        """Hand one line to the system, without waiting for the disk.

        Args:
            line: The line, newline included.

        Returns:
            Its number, for `sync`.
        """
        with self._write_lock:  # several workers write at once (0149)
            self._stream.write(line)
            self._stream.flush()
            self._written += 1
            return self._written

    def sync(self, number: int) -> None:
        """Return once the line `number`, and every line before it, is on the disk.

        Args:
            number: What `append` returned.
        """
        with self._sync_lock:
            if self._synced >= number:  # an `fsync` started after it already ran
                return
            with self._write_lock:
                covered = self._written  # this `fsync` carries them all
            os.fsync(self._stream.fileno())
            self._synced = covered
            self.syncs += 1

    def close(self) -> None:
        """Sync what is left (the last `done` lines), then close the stream."""
        try:
            self.sync(self._written)
        finally:
            self._stream.close()
