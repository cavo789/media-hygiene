"""Collaborators shared by the scan steps, bundled to keep signatures short."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.constants import Sizes

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.index.repository import FactsRepository
    from media_hygiene.scan.progress import ProgressSink


@dataclass(frozen=True, slots=True)
class ScanDeps:
    """The index to read/write facts, and where to report progress."""

    repository: FactsRepository
    progress: ProgressSink
    io_slots: asyncio.Semaphore = field(
        default_factory=lambda: asyncio.Semaphore(Sizes.IO_CONCURRENCY),
    )


@dataclass(frozen=True, slots=True)
class IntegrityTools:
    """How to check files: a pool for image decoding, `ffprobe` for videos."""

    executor: Executor
    ffprobe: str | None
