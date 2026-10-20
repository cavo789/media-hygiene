"""Which files only a backup holds the user already dealt with (0245).

The files only in a backup go through the same recognition as the files back after
being set aside (0216, `ReturnedFinder`): the contents the journals remember (set aside
by a choice, deletions confirmed), then the deletions still waiting for `review --gone`
(0224), whose size and digests the index kept. Only the files of a size remembered are
read; the others are proposed without reading them.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.index.gone_rows import gone_records
from media_hygiene.plan.backup_import import DealtWith
from media_hygiene.plan.returned import Remembered, RememberedSet
from media_hygiene.scan.exact import ExactDuplicateFinder
from media_hygiene.services.returned import ReturnedFinder

if TYPE_CHECKING:
    from media_hygiene.plan.backups import BackupComparison
    from media_hygiene.scan.deps import ScanDeps
    from media_hygiene.services.audit_analysis import Finders
    from media_hygiene.services.runtime import Runtime


def gone_finder(runtime: Runtime, deps: ScanDeps) -> ReturnedFinder | None:
    """Recognise the contents of the files deleted, waiting for an answer (0224).

    Args:
        runtime: Settings, mount points and output.
        deps: The audit's index, progress and I/O limit.

    Returns:
        The finder, or None when nothing waits.
    """
    by_digest: dict[tuple[int, str], Remembered] = {}
    by_partial: dict[tuple[int, str], Remembered] = {}
    for record in gone_records(deps.repository.connection):
        at = datetime.fromisoformat(record.gone_at) if record.gone_at else None
        said = Remembered(
            "",
            at or datetime.now(UTC),
            ActionKind.MARK_GONE,
            runtime.mapper.to_host(Path(record.path)),
        )
        by_partial[record.size, record.partial_digest] = said
        if record.full_digest:
            by_digest[record.size, record.full_digest] = said
    if not by_partial:
        return None
    remembered = RememberedSet(by_digest=by_digest, by_partial=by_partial)
    return ReturnedFinder(ExactDuplicateFinder(deps), remembered)


async def dealt_with(compared: BackupComparison, finders: Finders) -> BackupComparison:
    """Tell, for each backup, which of its own files were dealt with before.

    Args:
        compared: The library's groups and each backup's coverage.
        finders: The recognisers of what was set aside, and of what was deleted.

    Returns:
        The same comparison, each coverage knowing what not to propose.
    """
    only = [file for coverage in compared.folders for file in coverage.only]
    if not only:
        return compared
    aside = await finders.returned.find(only) if finders.returned else ()
    deleted = await finders.gone.find(only) if finders.gone else ()
    dealt = DealtWith(
        set_aside=frozenset(found.file.path for found in aside),
        deleted=frozenset(found.file.path for found in deleted)
        - frozenset(found.file.path for found in aside),
    )
    return replace(
        compared,
        folders=tuple(replace(coverage, dealt=dealt) for coverage in compared.folders),
    )
