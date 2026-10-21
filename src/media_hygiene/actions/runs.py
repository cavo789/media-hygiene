"""Run identifiers and the per-run history derived from journals."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.actions.journal import (
    JournalEntry,
    done_states,
    journal_file,
    read_journal,
)
from media_hygiene.actions.kinds import (
    ACTING_PHASES,
    BACKUP_SET_ASIDE,
    COPIES,
    FOLDER_ACTIONS,
    LEFT_IN_PLACE,
    LINKS,
    MARKS,
    MOVES,
    XMP_ACTIONS,
    ActionKind,
    Phase,
)
from media_hygiene.actions.quarantine import QUARANTINED
from media_hygiene.constants import JOURNAL_SUFFIX

if TYPE_CHECKING:
    from pathlib import Path

_RUN_ID_FORMAT: Final = "%Y%m%d-%H%M%S"
# Every run identifier: the stamp, then a number when two runs share a second.
RUN_ID_PATTERN: Final = re.compile(r"\d{8}-\d{6}(?:-\d+)?")


def new_run_id(journal_dir: Path) -> str:
    """Create a unique run identifier in local time, such as `20260925-183015`.

    Args:
        journal_dir: Where journals live, to avoid collisions.

    Returns:
        A fresh identifier.
    """
    base = datetime.now().astimezone().strftime(_RUN_ID_FORMAT)
    run_id, suffix = base, 1
    while journal_file(journal_dir, run_id).exists():
        suffix += 1
        run_id = f"{base}-{suffix}"
    return run_id


def run_phase(entries: list[JournalEntry]) -> Phase:
    """Tell which command made a run: the phase of its first action.

    Journals written before 0.3 hold `clean` entries only, and read as such.

    Args:
        entries: Journal entries, in write order.

    Returns:
        `clean`, `sort` or `album`; `clean` for a run that did nothing yet.
    """
    phases = (entry.phase for entry in entries if entry.phase in ACTING_PHASES)
    return next(phases, Phase.CLEAN)


@dataclass(frozen=True, slots=True)
class Kept:
    """The files a run left in place: moved, linked, or given a sidecar."""

    moved: int = 0
    linked: int = 0  # hard links: an album's (nothing freed), a copy's (its bytes)
    written: int = 0  # the sidecars `xmp` created or rewrote
    copied: int = 0  # bytes copied by `import`, or by `mh backup` to its target (0264)


@dataclass(frozen=True, slots=True)
class RunSummary:  # pylint: disable=too-many-instance-attributes
    """What a run did (`clean`, `sort` or `album`), and whether it was undone."""

    run_id: str
    kind: Phase
    deleted: int
    freed: int
    quarantined: int
    kept: Kept
    restored: int
    unwanted: int = 0  # of `quarantined`: photos set aside in `review --junk`
    returned: int = 0  # of `quarantined`: set aside before, back since (0216)
    marked: int = 0  # files deleted in the Explorer, confirmed (0224)
    folders_removed: int = 0  # left empty, removed (0202)

    @property
    def moved(self) -> int:
        """Count the files a sort moved.

        Returns:
            Them.
        """
        return self.kept.moved

    @property
    def linked(self) -> int:
        """Count the hard links a run made: an album's, or copies keeping their name.

        Returns:
            Them.
        """
        return self.kept.linked


def summarize(journal_dir: Path, run_id: str) -> RunSummary:
    """Summarise one run from its journal.

    Args:
        journal_dir: Journal mount point.
        run_id: Identifier of the run.

    Returns:
        The run summary.
    """
    entries = read_journal(journal_file(journal_dir, run_id))
    kind = run_phase(entries)
    files = [
        entry
        for entry in done_states(entries, kind)
        if entry.action not in FOLDER_ACTIONS | MARKS
    ]
    moved = [entry for entry in files if entry.action in MOVES]
    linked = [entry for entry in files if entry.action in LINKS]
    written = sum(1 for entry in files if entry.action in XMP_ACTIONS)
    copied = sum(entry.size for entry in files if entry.action in COPIES)
    aside = QUARANTINED | BACKUP_SET_ASIDE  # `mh backup`'s `.removed` (0264)
    quarantined = [entry for entry in files if entry.action in aside]
    # Only a deleted file frees space: a quarantined one takes it until `purge`.
    deleted = [
        entry
        for entry in files
        if entry.action not in LEFT_IN_PLACE and entry.action not in QUARANTINED
    ]
    # A copy made a link frees its bytes too, its name stays (0213).
    freeing = [*deleted, *(e for e in linked if e.action is ActionKind.LINK_DUPLICATE)]
    return RunSummary(
        run_id=run_id,
        kind=kind,
        deleted=len(deleted),
        freed=sum(entry.size for entry in freeing),
        quarantined=len(quarantined),
        kept=Kept(len(moved), len(linked), written, copied),
        restored=len(done_states(entries, Phase.UNDO)),
        unwanted=sum(e.action is ActionKind.QUARANTINE_UNWANTED for e in quarantined),
        returned=sum(e.action is ActionKind.QUARANTINE_RETURNED for e in quarantined),
        marked=sum(e.action in MARKS for e in done_states(entries, kind)),
        folders_removed=sum(
            e.action is ActionKind.REMOVE_FOLDER for e in done_states(entries, kind)
        ),
    )


def list_run_ids(journal_dir: Path) -> list[str]:
    """List every run that has a journal, newest first.

    Ordered by when each run started (UTC, in its journal), not by name: names are
    in local time, which a zone change or the autumn clock change can reorder.

    Args:
        journal_dir: Journal mount point.

    Returns:
        The run identifiers.
    """
    if not journal_dir.is_dir():
        return []
    files = journal_dir.glob(f"*{JOURNAL_SUFFIX}")
    started = {path.name.removesuffix(JOURNAL_SUFFIX): _started(path) for path in files}
    return sorted(started, key=lambda run: (started[run], run), reverse=True)


def _started(journal: Path) -> datetime:
    """When a run started: its first journal entry, else the file's last change.

    Args:
        journal: The run's journal.

    Returns:
        An aware UTC moment.
    """
    with journal.open(encoding="utf-8") as lines:
        first = lines.readline()
    try:
        return JournalEntry.model_validate_json(first).at
    except ValidationError:
        return datetime.fromtimestamp(journal.stat().st_mtime, UTC)
