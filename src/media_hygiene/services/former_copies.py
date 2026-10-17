"""The copies of kept files a clean removed, read from its journal (0207)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import REMOVED_COPIES
from media_hygiene.classify.former import FormerCopy
from media_hygiene.services.classify_inputs import root_of

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.services.runtime import Runtime


def removed_copies(
    runtime: Runtime, done: Sequence[JournalEntry]
) -> list[tuple[str, FormerCopy]]:
    """The copies of kept files a run removed, with the mounted folder each lay in.

    Exact copies deleted or set aside and near duplicates set aside; burst shots and
    the files set aside by choice are no copies of a file kept.

    Args:
        runtime: Mount points.
        done: The actions of the run carried out.

    Returns:
        The kept file's path and the copy, for each copy.
    """
    roots = runtime.mounts.data_roots(runtime.locations.data_dir)
    return [
        (entry.keeper, FormerCopy(copy, root_of(copy, roots, runtime)))
        for entry in done
        if entry.keeper and entry.action in REMOVED_COPIES
        for copy in (Path(entry.path),)
    ]
