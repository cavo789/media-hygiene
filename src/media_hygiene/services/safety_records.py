r"""Where the last push and the last backup are read from (0689).

`mh push` journals its renames and copies in `/journal` (`push_journal`): the newest
push run, whether it ended (nothing left `pending`) and the Windows path of its target
are read from there, through the facts `run_book` keeps. `mh backup` writes to
`/backups`, mounted for that command only: it leaves a note in `/cache`
(`BACKUP_NOTE`) with the archive's Windows path, so the home page can tell when it
ran and whether the archive is off this PC.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.run_stamps import run_started
from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.services.run_facts import RunFacts
    from media_hygiene.services.runtime import Runtime

BACKUP_NOTE: Final = "backup-made.json"
_UNC: Final = "\\\\"
_SYSTEM_DRIVE: Final = "c"
_DRIVE: Final = re.compile(r"^([A-Za-z]):")


@dataclass(frozen=True, slots=True)
class LastPush:
    """The newest `mh push` run of the journal."""

    started: datetime
    complete: bool  # every rename of it `done`
    host: str | None  # a Windows path in the target; None: nothing copied nor moved


@dataclass(frozen=True, slots=True)
class LastBackup:
    """The newest `mh backup`, as its note says."""

    made: datetime
    host: str  # the archive, as Windows sees it


def off_pc(host: str | None) -> bool | None:
    r"""Tell whether a Windows path is off this PC's system disk.

    Args:
        host: `\\NAS\share\…`, `E:\…`, `C:\…`, or None.

    Returns:
        True for a share or another drive than `C:`, False for `C:`, None when
        the path says nothing (unknown, or a Linux path).
    """
    if not host:
        return None
    if host.startswith(_UNC):
        return True
    drive = _DRIVE.match(host)
    if drive is None:
        return None
    return drive.group(1).lower() != _SYSTEM_DRIVE


def last_push(runs: Sequence[RunFacts]) -> LastPush | None:
    """Find the newest push run of the journal.

    Args:
        runs: Every run's facts, newest first (`run_book`).

    Returns:
        It; None when `mh push` never left a journal.
    """
    for facts in runs:
        if facts.push is not None:
            return LastPush(
                run_started(facts.run_id), facts.push.complete, facts.push.host
            )
    return None


def note_backup(runtime: Runtime, host: str) -> None:
    """Leave the note of a backup just written and read back, in `/cache`.

    Args:
        runtime: Settings and mount points.
        host: The archive, as Windows sees it.
    """
    if not runtime.persistent(MountKind.CACHE):
        return
    note = {"made": datetime.now().astimezone().isoformat(), "host": host}
    path = runtime.locations.cache_dir / BACKUP_NOTE
    draft = path.with_suffix(".part")
    draft.write_text(json.dumps(note), "utf-8")
    draft.replace(path)


def last_backup(cache_dir: Path) -> LastBackup | None:
    """Read the note of the newest backup.

    Args:
        cache_dir: Cache mount point.

    Returns:
        It; None when no backup left a note, or the note does not read.
    """
    try:
        note = json.loads((cache_dir / BACKUP_NOTE).read_text("utf-8"))
        return LastBackup(datetime.fromisoformat(note["made"]), str(note["host"]))
    except OSError, ValueError, KeyError, TypeError:
        return None
