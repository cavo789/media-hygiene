"""After `shrink`: the originals set aside leave the index, parked for `undo`.

Like `clean` (`index.parked`): the rows of an original moved to the quarantine are
parked under the run, `undo` puts them back, `purge` drops them. The listings of the
folders the run changed are forgotten: the next audit reads them again and describes
the lighter videos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import done_states
from media_hygiene.actions.kinds import Phase
from media_hygiene.index.parked import park
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.touched_folders import forget_listings

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.services.runtime import Runtime


def park_originals(runtime: Runtime, run_id: str, entries: list[JournalEntry]) -> None:
    """Park the index rows of the originals a run set aside.

    Args:
        runtime: Settings, mount points and output.
        run_id: The run.
        entries: Its journal.
    """
    index = runtime.index_file
    if index is None or not index.is_file():
        return
    done = done_states(entries, Phase.SHRINK)
    aside = [(entry.path, entry.quarantine) for entry in done if entry.quarantine]
    with FactsRepository.open(index) as repository:
        park(repository.connection, run_id, aside)
        forget_listings(repository.connection, done)
