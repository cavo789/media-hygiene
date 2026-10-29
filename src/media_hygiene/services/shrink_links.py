"""After `shrink` or its `undo`: the files naming a renamed video follow it (0418).

`shrink` writes the lighter video of an `.avi` (or any non-`.mp4`) as an `.mp4`: an
album, a review decision or a chosen video naming the original would then name a
file in the quarantine. The rewrite of `sort` (0382, `follow_links`) is reused, both
ways: `shrink` gives the new name, its `undo` gives the original's name back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import done_states, read_journal
from media_hygiene.actions.kinds import ActionKind, Phase

if TYPE_CHECKING:
    from pathlib import Path


def renamed(journal: Path, phase: Phase) -> list[tuple[str, str]]:
    """The videos a run renamed: old and new container path.

    Args:
        journal: The journal of the run.
        phase: `shrink` (original → lighter video) or `undo` (lighter → original).

    Returns:
        The renames, without the videos that kept their name.
    """
    done = done_states(read_journal(journal), phase)
    pairs = [
        (entry.keeper, entry.path)
        for entry in done
        if entry.action is ActionKind.SHRUNK
        and entry.keeper
        and entry.keeper != entry.path
    ]
    if phase is Phase.UNDO:
        return [(new, old) for old, new in pairs]
    return pairs
