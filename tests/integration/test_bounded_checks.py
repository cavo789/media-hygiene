"""The integrity pass hands the pool a bounded number of files at once (0151)."""

from __future__ import annotations

import asyncio
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Final, override

from media_hygiene.constants import MediaKind
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan import broken, file_check
from media_hygiene.scan.broken import BrokenFileFinder
from media_hygiene.scan.deps import IntegrityTools, ScanDeps
from media_hygiene.scan.image_check import ImageInspection
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest

_IN_FLIGHT: Final = 4
_FILES: Final = 60


class CountingPool(ThreadPoolExecutor):
    """A thread pool that remembers the most work it ever held at once."""

    def __init__(self) -> None:
        """Two threads, nothing submitted yet."""
        super().__init__(max_workers=2)
        self._lock = threading.Lock()
        self.outstanding = 0
        self.peak = 0

    @override
    def submit[T](
        self, fn: Callable[..., T], /, *args: object, **kwargs: object
    ) -> Future[T]:
        """Count the work until it ends."""
        with self._lock:
            self.outstanding += 1
            self.peak = max(self.peak, self.outstanding)
        future = super().submit(fn, *args, **kwargs)
        future.add_done_callback(self._finished)
        return future

    def _finished[T](self, _future: Future[T]) -> None:
        """One less piece of work held."""
        with self._lock:
            self.outstanding -= 1


def test_integrity_pass_holds_a_bounded_number_of_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """60 pictures, at most 4 handed to the pool at any time, every one checked."""

    def healthy(_path: Path) -> ImageInspection:
        return ImageInspection()

    monkeypatch.setattr(file_check, "inspect_image", healthy)
    monkeypatch.setattr(broken, "pool_in_flight", lambda: _IN_FLIGHT)
    files = [
        MediaFile(Path(f"/data/x/{index}.jpg"), 10 + index, 1, MediaKind.IMAGE)
        for index in range(_FILES)
    ]
    with FactsRepository.open(None) as index, CountingPool() as pool:
        finder = BrokenFileFinder(
            ScanDeps(index, NullProgress()), IntegrityTools(pool, None)
        )
        found = asyncio.run(finder.find(files))
        assert pool.peak <= _IN_FLIGHT
        assert not found.broken
        assert all(index.get(file).integrity_checked for file in files)
