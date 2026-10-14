"""A long pass stores each file as it ends: a run stopped halfway keeps them (0143)."""

from __future__ import annotations

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.constants import MediaKind
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan import file_check
from media_hygiene.scan.broken import BrokenFileFinder
from media_hygiene.scan.deps import IntegrityTools, ScanDeps
from media_hygiene.scan.exact import ExactDuplicateFinder
from media_hygiene.scan.hashing import partial_digest
from media_hygiene.scan.image_check import ImageInspection, inspect_image
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress
from tests.support.media import MediaFactory

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# Long enough for the first file's result to reach the event loop before the failure.
_SETTLE_SECONDS: Final = 0.3


class StoppedError(RuntimeError):
    """The failure that ends the pass halfway, standing for a kill."""


def listed(path: Path) -> MediaFile:
    """The file as the scan lists it."""
    stat = path.stat()
    return MediaFile(path, stat.st_size, stat.st_mtime_ns, MediaKind.IMAGE)


def first_then_fail[T](first: Path, work: Callable[[Path], T]) -> Callable[[Path], T]:
    """Do the real work on `first`; on any other file, wait for it, then fail."""
    done = threading.Event()

    def run(path: Path) -> T:
        if path != first:
            done.wait()
            time.sleep(_SETTLE_SECONDS)
            raise StoppedError
        result = work(path)
        done.set()
        return result

    return run


def two_photos(tmp_path: Path) -> tuple[MediaFile, MediaFile]:
    """Two photos of the same size (so both are hashed), the first one real."""
    media = MediaFactory(tmp_path)
    first = media.image("a.jpg", seed=1)
    second = media.copy(first, "b.jpg")
    return listed(first), listed(second)


def test_checked_photo_is_stored_before_the_pass_ends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The integrity pass: the photo checked first is in the index."""
    done, failing = two_photos(tmp_path)
    check: Callable[[Path], ImageInspection] = first_then_fail(done.path, inspect_image)
    monkeypatch.setattr(file_check, "inspect_image", check)
    with (
        FactsRepository.open(None) as index,
        ThreadPoolExecutor(max_workers=2) as executor,
    ):
        finder = BrokenFileFinder(
            ScanDeps(index, NullProgress()), IntegrityTools(executor, None)
        )
        with pytest.raises(ExceptionGroup):
            asyncio.run(finder.find([done, failing]))
        assert index.get(done).integrity_checked
        assert not index.get(failing).integrity_checked


def test_hashed_file_is_stored_before_the_pass_ends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exact-duplicate pass: the file hashed first is in the index."""
    done, failing = two_photos(tmp_path)
    digest = first_then_fail(done.path, partial_digest)
    monkeypatch.setattr("media_hygiene.scan.exact.partial_digest", digest)
    with FactsRepository.open(None) as index:
        finder = ExactDuplicateFinder(ScanDeps(index, NullProgress()))
        with pytest.raises(ExceptionGroup):
            asyncio.run(finder.find([done, failing]))
        assert index.get(done).partial_digest is not None
        assert index.get(failing).partial_digest is None
