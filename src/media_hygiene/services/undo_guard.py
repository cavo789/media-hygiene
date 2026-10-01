"""The guards of `undo`: what reversing a run needs, checked before anything changes.

`undo` acts like `clean` and `sort` (a persistent journal, no read-only folder), but
it moves nothing to the quarantine: it needs `/quarantine` only to bring back what a
run put there.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.quarantine import QUARANTINED
from media_hygiene.actions.undo import actions_to_undo
from media_hygiene.errors import MountError
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.acting import ensure_can_act

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.services.runtime import Runtime


def ensure_undo_ready(runtime: Runtime, run_ids: Sequence[str]) -> None:
    """Refuse to undo runs that cannot be undone safely and completely.

    Args:
        runtime: Settings, mount points and output.
        run_ids: The runs about to be undone.

    Raises:
        MountError: The journal is not persistent, a folder is read-only, a mount point
            is not writable, or a run has files in a quarantine that is not mounted.
    """
    ensure_can_act(runtime, Phase.UNDO.value)
    if runtime.persistent(MountKind.QUARANTINE):
        return
    for run_id in run_ids:
        count = quarantined_count(runtime, run_id)
        if count:
            raise MountError(
                ngettext(
                    "The run {run_id} moved {count} file to /quarantine, which is "
                    "not mounted: nothing was changed.",
                    "The run {run_id} moved {count} files to /quarantine, which is "
                    "not mounted: nothing was changed.",
                    count,
                ).format(run_id=run_id, count=count),
                _(
                    'Mount the same quarantine folder as for that run: -v "<folder>:'
                    '/quarantine".'
                ),
            )


def quarantined_count(runtime: Runtime, run_id: str) -> int:
    """Count the files of a run still waiting in the quarantine for their undo.

    Args:
        runtime: Settings, mount points and output.
        run_id: An existing run.

    Returns:
        How many of its actions not undone yet are quarantine moves.
    """
    entries = read_journal(journal_file(runtime.locations.journal_dir, run_id))
    return sum(entry.action in QUARANTINED for entry in actions_to_undo(entries))
