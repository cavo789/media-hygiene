"""After a `sort`, `album` or `xmp` run: the folders it changed are read again."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import done_states, journal_file, read_journal
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.touched_folders import forget_listings

if TYPE_CHECKING:
    from media_hygiene.actions.kinds import Phase
    from media_hygiene.services.runtime import Runtime


def forget_run_listings(runtime: Runtime, run_id: str, phase: Phase) -> None:
    """Forget the listings of the folders a run changed (`index.touched_folders`).

    Args:
        runtime: Settings, mount points and output.
        run_id: The run just done.
        phase: The command that ran it.
    """
    index = runtime.index_file
    if index is None or not index.is_file():
        return
    file = journal_file(runtime.locations.journal_dir, run_id)
    done = done_states(read_journal(file), phase)
    if not done:
        return
    with FactsRepository.open(index) as repository:
        forget_listings(repository.connection, done)
