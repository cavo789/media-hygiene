"""`spots`: fill the index for the photos already there (0545), like the audit does."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.spot_rows import spot_figures
from media_hygiene.services.spot_fill import fill_spots

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.index.spot_rows import SpotFigures
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class SpotScan:
    """How many rows this run wrote; the figures read back from the index."""

    written: int
    figures: SpotFigures


def spot_index(runtime: Runtime) -> Path:
    """The index the rows live in.

    Args:
        runtime: Mount points.

    Returns:
        Its file.

    Raises:
        MountError: The cache holds no index yet.
    """
    index = runtime.index_file
    if index is None or not index.is_file():
        raise MountError(
            _("No index yet: nothing to name."),
            _("Run 'audit' with the same /cache mount first."),
        )
    return index


def scan_spots(runtime: Runtime, progress: ProgressSink) -> SpotScan:
    """Fill the rows missing, then count what the index holds.

    Args:
        runtime: Settings, mount points.
        progress: Where the progress line goes.

    Returns:
        What was done, read back.

    Raises:
        MountError: The cache holds no index yet.
    """
    with FactsRepository.open(spot_index(runtime)) as repository:
        written = fill_spots(runtime, repository.connection, progress)
        return SpotScan(written, spot_figures(repository.connection))
