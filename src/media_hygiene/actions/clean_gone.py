"""The marks `clean --decisions` writes for the files deleted in the Explorer (0224).

A file gone that the user confirmed deleted on purpose gets a `mark-gone` line in the
run's journal, with its size and digests: nothing moves, but the content is
remembered, and set aside again if it comes back. `undo` of the run forgets it.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.constants import MediaKind
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from media_hygiene.actions.journaled import JournaledChanges
    from media_hygiene.plan.models import CleanPlan


def mark_gone(changes: JournaledChanges, plan: CleanPlan) -> None:
    """Journal a mark per file deleted on purpose; nothing is counted nor moved.

    Args:
        changes: The journaled changes of the run.
        plan: What to clean, with the answers of `review --gone`.
    """
    for answer in plan.gone:
        if not answer.deleted:
            continue
        record = answer.record
        file = MediaFile(
            Path(record.path), record.size, record.mtime_ns, MediaKind.SIDECAR
        )
        entry = changes.entry(file, ActionKind.MARK_GONE).model_copy(
            update={"sha256": record.full_digest, "partial": record.partial_digest}
        )
        changes.record(entry, lambda: None)
