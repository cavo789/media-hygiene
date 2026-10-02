"""Find the files of an album where they are now, and keep those with enough stars.

A row of the plan is where the plan saw it, unless a `sort` of that plan moved it: the
journals say where. A file no longer there, or of another size, is listed as missing:
never linked on a guess. The stars come from the index, as the audit read them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.album_plan import Pick
from media_hygiene.actions.sort_moves import file_of
from media_hygiene.actions.sort_resume import moved_targets
from media_hygiene.errors import AlbumError
from media_hygiene.i18n import _
from media_hygiene.index.repository import FactsRepository

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.classify.plan_file import PlanRow
    from media_hygiene.services.runtime import Runtime


def find_picks(
    runtime: Runtime, plan_id: str, rows: Sequence[PlanRow]
) -> tuple[list[Pick], tuple[Path, ...]]:
    """Find each row's file: where a sort moved it, else where the plan saw it.

    Args:
        runtime: Settings, mount points and output.
        plan_id: The classify plan the rows come from.
        rows: The rows selected.

    Returns:
        The files found, and the paths of those missing (container paths).
    """
    moved = moved_targets(runtime.locations.journal_dir, plan_id)
    picks: list[Pick] = []
    missing: list[Path] = []
    for row in rows:
        path = moved.get(row.id) or runtime.mapper.to_container(row.path)
        try:
            info = path.stat()
        except OSError:
            missing.append(path)
            continue
        if not path.is_file() or info.st_size != row.size:
            missing.append(path)
            continue
        picks.append(Pick(path, info.st_size, info.st_mtime_ns))
    return picks, tuple(missing)


def rated(runtime: Runtime, picks: list[Pick], stars: int) -> list[Pick]:
    """Keep the files given at least so many stars in Windows.

    Args:
        runtime: Settings, mount points and output.
        picks: The files found.
        stars: The fewest stars; 0 keeps every file.

    Returns:
        The files kept, in the same order.

    Raises:
        AlbumError: The stars are asked for, but the index is not mounted.
    """
    if not stars:
        return picks
    index = runtime.index_file
    if index is None:
        raise AlbumError(
            _(
                "--rating reads the stars the audit wrote in its cache, which is not "
                "mounted."
            ),
            _('Mount the same cache folder as for the audit: -v "<folder>:/cache".'),
        )
    kept: list[Pick] = []
    with FactsRepository.open(index) as repository:
        for pick in picks:
            facts = repository.get(file_of(pick.source, (pick.size, pick.mtime_ns)))
            rating = facts.metadata.rating if facts.metadata else None
            if rating is not None and rating >= stars:
                kept.append(pick)
    return kept
