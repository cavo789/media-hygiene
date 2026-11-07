"""After an undo, the index follows the files moved back (they keep their facts)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import done_states, read_journal
from media_hygiene.actions.kinds import REMOVED_COPIES, ActionKind, Phase
from media_hygiene.index.former_names import forget_former
from media_hygiene.index.parked import unpark
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.touched_folders import forget_listings
from media_hygiene.services.undo_landmarks import refresh_landmarks

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.services.drive_letter import LetterChange
    from media_hygiene.services.runtime import Runtime


def follow_moves_back(
    runtime: Runtime, run: tuple[Path, str], changes: Sequence[LetterChange]
) -> list[tuple[str, str]]:
    """Update the index: files moved back by `undo` keep their facts.

    The index knows them by the paths of the run, under the drive's old letter. A
    copy back under its own name is no longer remembered by its kept file.

    Args:
        runtime: Settings, mount points and output.
        run: The journal of the run, and the run.
        changes: The drives of the run that changed letter since.

    Returns:
        The files moved back: where the run had put them, where they are now.
    """
    index = runtime.index_file
    done = done_states(read_journal(run[0]), Phase.UNDO)
    back = [
        (_known(entry.target, changes), entry.path)
        for entry in done
        if entry.action is ActionKind.MOVE and entry.target
    ]
    restored = [(_known(e.quarantine, changes), e.path) for e in done if e.quarantine]
    copies = [
        _known(entry.path, changes) for entry in done if entry.action in REMOVED_COPIES
    ]
    if index is None or not done:
        return back
    with FactsRepository.open(index) as repository:
        repository.move(back)
        unpark(repository.connection, restored)  # set aside by a clean (0156)
        forget_former(repository.connection, run[1], copies)
        forget_listings(repository.connection, done)  # the folders read again
        refresh_landmarks(repository.connection, done)  # a landmark typed (0650)
    return back


def _known(path: str, changes: Sequence[LetterChange]) -> str:
    """The path the index knows a file by: under the drive's letter of the run.

    Args:
        path: A path the undo used, under today's letter.
        changes: The drives of the run that changed letter.

    Returns:
        The path under the old letter.
    """
    for change in changes:
        path = change.back(path) or path
    return path
