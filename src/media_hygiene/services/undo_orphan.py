"""`undo --from-quarantine <run>` (0687): the way back of a run whose journal is lost.

A run's quarantine mirrors the photo folders: `<quarantine>/<run>/c/Photos/x.jpg`
was `/data/c/Photos/x.jpg`, whichever quarantine (the default one, or a drive's own,
even mounted under another letter) holds it. The moves back are rebuilt from that
layout alone, shown first, then each file goes back only where nothing is (never over
a file), only into a photo drive that is mounted, and is proven by reading its size
back from the disk. Deleted copies (`clean --delete`) cannot come back this way: only
a journal names them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.no_overwrite import move_no_replace
from media_hygiene.actions.purge import run_folders
from media_hygiene.actions.quarantine import LeftFolders
from media_hygiene.errors import JournalError
from media_hygiene.i18n import _
from media_hygiene.services.quarantines import mounted_quarantines

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class OrphanMove:
    """One file of the quarantine and the place it came from."""

    quarantined: Path
    original: Path
    size: int


@dataclass(frozen=True, slots=True)
class OrphanPlan:
    """What `--from-quarantine` would do: moves, and files left with the reason."""

    run_id: str
    moves: tuple[OrphanMove, ...]
    left: tuple[tuple[Path, str], ...]  # (quarantined file, why it stays)


@dataclass(frozen=True, slots=True)
class OrphanOutcome:
    """The files proven back, and those left in the quarantine with the reason."""

    back: tuple[Path, ...]
    left: tuple[tuple[Path, str], ...]


def orphan_plan(runtime: Runtime, run_id: str) -> OrphanPlan:
    """Rebuild the moves back of a run from its quarantine's layout.

    Args:
        runtime: Settings, mount points and output.
        run_id: The run, named like the folder of the quarantine.

    Returns:
        The moves, and the files that cannot go back.

    Raises:
        JournalError: The run still has its journal (plain `undo` is exact), or no
            quarantine holds it.
    """
    if journal_file(runtime.locations.journal_dir, run_id).is_file():
        raise JournalError(
            _("The run {run_id} still has its journal.").format(run_id=run_id),
            _("Type mh undo {run_id}: it is exact.").format(run_id=run_id),
        )
    folders = run_folders(mounted_quarantines(runtime).folders, run_id)
    if not folders:
        raise JournalError(
            _("No quarantine holds the run {run_id}.").format(run_id=run_id),
            _("Plug in the drive of its quarantine."),
        )
    data = runtime.locations.data_dir
    moves: list[OrphanMove] = []
    left: list[tuple[Path, str]] = []
    for folder in folders:
        for file in sorted(p for p in folder.rglob("*") if p.is_file()):
            original = data / file.relative_to(folder)
            why = _why_left(original, data)
            if why is None:
                moves.append(OrphanMove(file, original, file.stat().st_size))
            else:
                left.append((file, why))
    return OrphanPlan(run_id, tuple(moves), tuple(left))


def _why_left(original: Path, data: Path) -> str | None:
    """Tell why a file cannot go back to its place, or None when it can.

    Args:
        original: Its place, under the data mount.
        data: The data mount point.

    Returns:
        The reason, translated, or None.
    """
    drive = data / original.relative_to(data).parts[0]
    if not drive.is_dir():
        return _("its drive is not mounted (or changed letter)")
    if original.exists():
        return _("a file is already at its place")
    return None


def apply_orphan_plan(plan: OrphanPlan) -> OrphanOutcome:
    """Move each file back, never over another, proven by its size on the disk.

    Args:
        plan: The moves shown to the user.

    Returns:
        The files back, and those left (with the plan's own).
    """
    back: list[Path] = []
    left = list(plan.left)
    emptied = LeftFolders()
    for move in plan.moves:
        try:
            move_no_replace(move.quarantined, move.original)
        except FileExistsError:
            left.append((move.quarantined, _("a file is already at its place")))
            continue
        except OSError as error:
            left.append((move.quarantined, str(error)))
            continue
        if move.original.stat().st_size == move.size and not move.quarantined.exists():
            back.append(move.original)
            emptied.note(move.original, move.quarantined)
        else:
            left.append((move.quarantined, _("it did not read back whole")))
    emptied.remove()
    return OrphanOutcome(tuple(back), tuple(left))
