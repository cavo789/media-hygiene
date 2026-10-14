"""After a walk, forget the indexed files that are gone — only where the walk proves it.

A file absent from the walk is gone only if the walk could have seen it: below a folder
mounted this time, not below a folder it could not read or chose to skip, with an
extension this run analyses. Anything else is kept: another disk audited another day, a
disk that hiccuped, an excluded folder, a `--ext` run.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.index.rematch import rematched
from media_hygiene.index.walks import mark_walked
from media_hygiene.paths.host_paths import is_within

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.index.repository import FactsRepository
    from media_hygiene.scan.filters import ScanFilters
    from media_hygiene.scan.models import MediaFile

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WalkCoverage:
    """What one walk saw: its roots, the files it listed, what it could not read."""

    roots: tuple[Path, ...]
    listed: frozenset[str]
    unreadable: tuple[Path, ...]
    filters: ScanFilters
    files: Sequence[MediaFile] = ()  # what was listed: the moved files are among them


@dataclass(frozen=True, slots=True)
class Pruned:
    """What the index did after a walk: files followed to their new path, forgotten."""

    followed: int = 0
    forgotten: int = 0


def forget_missing(repository: FactsRepository, coverage: WalkCoverage) -> Pruned:
    """Follow the files moved since, forget the other ones the walk proves gone.

    A file moved or renamed outside the tool keeps its rows (`index.rematch`); the
    other gone files are forgotten. The complete walks are dated.

    Args:
        repository: The index.
        coverage: What the walk saw.

    Returns:
        How many files were followed, and how many forgotten.
    """
    indexed = {root: repository.paths_under(root) for root in coverage.roots}
    gone = [
        path
        for root, paths in indexed.items()
        for path in paths
        if _proven_gone(Path(path), root, coverage)
    ]
    known = {path for paths in indexed.values() for path in paths}
    newcomers = [file for file in coverage.files if str(file.path) not in known]
    pairs = rematched(repository.connection, gone, newcomers) if gone else []
    repository.move(pairs)
    followed = {old for old, _new in pairs}
    forgotten = repository.forget(path for path in gone if path not in followed)
    _LOGGER.debug("Index: forgot %d files that are gone", forgotten)
    now = datetime.now(UTC)
    for root in coverage.roots:
        if not any(is_within(item, root) for item in coverage.unreadable):
            mark_walked(repository, root, now)
    return Pruned(len(pairs), forgotten)


def _proven_gone(path: Path, root: Path, coverage: WalkCoverage) -> bool:
    """Tell whether the walk would have listed this file, had it still existed.

    Args:
        path: An indexed file below `root`.
        root: The mounted folder walked.
        coverage: What the walk saw.

    Returns:
        True when it was not listed although the walk could see it.
    """
    if str(path) in coverage.listed or not coverage.filters.accepts(path):
        return False
    if any(is_within(path, item) for item in coverage.unreadable):
        return False
    folders = path.parents[: len(path.parents) - len(root.parents) - 1]
    return not any(coverage.filters.skips_dir(folder) for folder in folders)
