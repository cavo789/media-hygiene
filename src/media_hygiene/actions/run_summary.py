"""What a run did, from its journal entries: pure, no file read (split from `runs`)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import done_states
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

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry


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
    copied: int = 0  # bytes copied by `import`, or by `mh push` to its target (0264)


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


def summary_of(entries: list[JournalEntry], run_id: str) -> RunSummary:
    """Summarise one run from its entries.

    Args:
        entries: The run's journal entries.
        run_id: Identifier of the run.

    Returns:
        The run summary.
    """
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
    aside = QUARANTINED | BACKUP_SET_ASIDE  # `mh push`'s `.removed` (0264)
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
