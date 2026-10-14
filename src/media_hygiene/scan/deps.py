"""Collaborators shared by the scan steps, bundled to keep signatures short."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.constants import Sizes
from media_hygiene.scan.first_checks import CheckReporter, SilentReporter
from media_hygiene.scan.whole_read import WHOLE_READ_LIMIT

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.index.repository import FactsRepository
    from media_hygiene.scan.progress import ProgressSink


@dataclass(frozen=True, slots=True)
class ScanDeps:
    """The index to read/write facts, where to report progress and the pace."""

    repository: FactsRepository
    progress: ProgressSink
    io_slots: asyncio.Semaphore = field(
        default_factory=lambda: asyncio.Semaphore(Sizes.IO_CONCURRENCY),
    )
    reporter: CheckReporter = field(default_factory=SilentReporter)


@dataclass(frozen=True, slots=True)
class IntegrityTools:
    """How to check files: a pool for images, `ffprobe` and `ffmpeg` for videos.

    `read_limit`: the largest picture read once into memory, in bytes.
    """

    executor: Executor
    ffprobe: str | None
    ffmpeg: str | None = None
    read_limit: int = WHOLE_READ_LIMIT
