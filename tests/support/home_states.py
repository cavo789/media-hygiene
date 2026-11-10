"""The situations of the home page's mockup, written as the tool folders hold them.

Each one writes what `status` reads: a report's summary, a quarantine, a journal, a
classify proposal. First run, audit done, after the clean, after the import, the
quarantine freed, a proposal waiting, everything sorted.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.constants import CLASSIFY_PLAN_FILE_NAME, RunKind
from media_hygiene.services.safety_records import note_backup
from tests.support.journaled import done_line

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.services.runtime import Runtime

CLEAN_RUN: Final = "20261020-143210"
IMPORT_RUN: Final = "20261020-151144"
# After every proposal written by a test, whenever it runs.
SORT_RUN: Final = "20991231-235959"
OLD_PUSH_RUN: Final = "20200101-120000"
_STAMPS: Final = {
    RunKind.AUDIT: ("20261020-110300", "11:03"),
    RunKind.CLEAN: ("20261020-143210", "14:32"),
}


def report(runtime: Runtime, kind: RunKind, counts: tuple[int, int]) -> None:
    """Write the summary of an audit or a clean: extra copies, files only on the NAS."""
    copies, backup_only = counts
    stamp, time = _STAMPS[kind]
    folder = runtime.locations.reports_dir / f"{stamp}-{kind.value}"
    folder.mkdir(exist_ok=True)
    summary = {
        "folder": folder.name,
        "kind": kind.value,
        "created_at": f"2026-10-20T{time}:00+00:00",
        "files_scanned": 48213,
        "duplicate_groups": copies,
        "duplicate_files": copies,
        "reclaimable_bytes": 1000 * copies,
        "broken_files": 3,
        "backup_only": backup_only,
    }
    (folder / "summary.json").write_text(json.dumps(summary), "utf-8")


def journal(runtime: Runtime, run_id: str, entry: tuple[Phase, ActionKind]) -> None:
    """Write a run of one file done."""
    phase, action = entry
    # A quarantined file is undoable while its copy is in the quarantine (`blocker`).
    kept = runtime.locations.quarantine_dir / CLEAN_RUN / "c" / "IMG_1.jpg"
    line = done_line(
        action, "/data/c/Photos/a.jpg", phase=phase, target="/data/c/b.jpg"
    ).model_copy(update={"quarantine": str(kept)})
    path = journal_file(runtime.locations.journal_dir, run_id)
    path.write_text(line.model_dump_json() + "\n", "utf-8")


def quarantined(runtime: Runtime) -> None:
    """A file of the clean run in the quarantine."""
    folder = runtime.locations.quarantine_dir / CLEAN_RUN / "c"
    folder.mkdir(parents=True)
    (folder / "IMG_1.jpg").write_bytes(b"x" * 10)


def proposed(runtime: Runtime) -> None:
    """A classify proposal."""
    folder = runtime.locations.reports_dir / "20261020-160200-classify"
    folder.mkdir()
    (folder / CLASSIFY_PLAN_FILE_NAME).write_text("{}", "utf-8")


def first_run(runtime: Runtime) -> None:
    """Nothing done yet."""
    del runtime


def audit_done(runtime: Runtime) -> None:
    """An audit found extra copies, and files only the NAS holds."""
    report(runtime, RunKind.AUDIT, (2941, 214))


def after_clean(runtime: Runtime) -> None:
    """The copies set aside: a clean report, its quarantine, its run undoable."""
    report(runtime, RunKind.AUDIT, (0, 214))
    report(runtime, RunKind.CLEAN, (0, 214))
    quarantined(runtime)
    journal(runtime, CLEAN_RUN, (Phase.CLEAN, ActionKind.QUARANTINE))


def after_import(runtime: Runtime) -> None:
    """Then the NAS's files copied back."""
    after_clean(runtime)
    journal(runtime, IMPORT_RUN, (Phase.IMPORT, ActionKind.COPY_IN))


def quarantine_freed(runtime: Runtime) -> None:
    """An audit with nothing left, the quarantine empty."""
    report(runtime, RunKind.AUDIT, (0, 0))


def proposal_waiting(runtime: Runtime) -> None:
    """A classify proposal not sorted yet."""
    quarantine_freed(runtime)
    proposed(runtime)


def all_sorted(runtime: Runtime) -> None:
    """The proposal applied by a sort since."""
    proposal_waiting(runtime)
    journal(runtime, SORT_RUN, (Phase.SORT, ActionKind.MOVE))


def pushed(runtime: Runtime, run_id: str, host: str) -> None:
    """A complete `mh push` run, of one copy into a target on `host` (0689)."""
    line = done_line(ActionKind.PUSH_COPY, "C/Photos", phase=Phase.PUSH, host_path=host)
    path = journal_file(runtime.locations.journal_dir, run_id)
    path.write_text(line.model_dump_json() + "\n", "utf-8")


def backed_up(runtime: Runtime, host: str) -> None:
    """The note `mh backup` leaves, the archive on `host` (0689)."""
    note_backup(runtime, host)


def old_push(runtime: Runtime) -> None:
    """A push to the NAS long ago, never a backup."""
    audit_done(runtime)
    pushed(runtime, OLD_PUSH_RUN, r"\\NAS\backup_photos\C\Photos")


def all_safe(runtime: Runtime) -> None:
    """A push to the NAS and a backup on a USB stick, both today."""
    quarantine_freed(runtime)
    now = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    pushed(runtime, now, r"\\NAS\backup_photos\C\Photos")
    backed_up(runtime, r"E:\mh-backups\mh-backup-1.zip")


SITUATIONS: Final[dict[str, Callable[[Runtime], None]]] = {
    "first run": first_run,
    "audit done": audit_done,
    "after clean": after_clean,
    "after import": after_import,
    "quarantine freed": quarantine_freed,
    "proposal waiting": proposal_waiting,
    "everything sorted": all_sorted,
}
