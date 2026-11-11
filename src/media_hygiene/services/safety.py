"""*Are my photos safe?* (0689): every fact of the card, read from disk each call.

The slow ones are kept in `/cache` while nothing they depend on changes (0692).

The second copy and where it is (the push journal), the tool's memory (the note of
`mh backup`), the way back (the journals, the quarantines mounted), what waits in the
quarantine and how much of it exists nowhere else (0688), the damaged files and how
far the re-read went (0690). The home page and `mh status` draw the same facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import journal_file
from media_hygiene.index.safety_counts import RereadCounts, newer_than, reread_counts
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.quarantines import mounted_quarantines
from media_hygiene.services.safety_cache import SlowAsk, slow_facts
from media_hygiene.services.safety_records import (
    LastBackup,
    LastPush,
    last_backup,
    last_push,
)

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.status_parts import QuarantineState

# A push or a backup older than this is said amber. Constants, not settings: a month
# is a month in every collection (the maintainer's rule, `few-settings`).
PUSH_FRESH_DAYS: Final = 30
BACKUP_FRESH_DAYS: Final = 30
_NS: Final = 1_000_000_000


@dataclass(frozen=True, slots=True)
class WayBack:
    """What `undo` can still put back."""

    journal: bool  # `/journal` is a persistent mount
    lost: int  # runs in the quarantine with no journal
    unplugged: tuple[str, ...]  # drives whose quarantine is not mounted


@dataclass(frozen=True, slots=True)
class SafetyFacts:  # pylint: disable=too-many-instance-attributes
    """Every fact the card reads; None where a mount or a record is missing."""

    now: datetime
    push: LastPush | None
    newer: int | None  # files of the index changed since the last push
    backup: LastBackup | None
    way_back: WayBack
    quarantine: QuarantineState
    only: int | None  # files of the quarantine that exist nowhere else
    reread: RereadCounts | None


def read_safety(runtime: Runtime, quarantine: QuarantineState) -> SafetyFacts:
    """Read every fact of the card.

    Args:
        runtime: Settings and mount points.
        quarantine: The quarantine as `status` measured it.

    Returns:
        The facts.
    """
    journal_dir = runtime.locations.journal_dir
    journal = runtime.persistent(MountKind.JOURNAL)
    push = last_push(journal_dir) if journal else None
    index = (
        runtime.locations.index_file if runtime.persistent(MountKind.CACHE) else None
    )
    runs = tuple(run.run_id for run in quarantine.runs)
    folders = mounted_quarantines(runtime).folders
    slow = slow_facts(SlowAsk(runtime, runs, folders)) if journal else None
    return SafetyFacts(
        now=datetime.now().astimezone(),
        push=push,
        newer=None
        if push is None
        else newer_than(index, int(push.started.timestamp() * _NS)),
        backup=last_backup(runtime.locations.cache_dir) if index else None,
        way_back=WayBack(
            journal,
            sum(not journal_file(journal_dir, run).is_file() for run in runs),
            slow.unplugged if slow is not None else (),
        ),
        quarantine=quarantine,
        only=slow.only if slow is not None else None,
        reread=reread_counts(index),
    )
