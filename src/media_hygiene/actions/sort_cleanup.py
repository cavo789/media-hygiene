"""Remove the source folders a sort emptied: junk to the quarantine, then the folder."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.outcome import Incident
from media_hygiene.actions.sort_folders import Fate, FolderReport, Verdict, verdicts
from media_hygiene.actions.sort_moves import file_of

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.actions.journaled import JournaledChanges
    from media_hygiene.actions.outcome import Tally
    from media_hygiene.actions.sort_folders import FolderRules

_LOGGER = logging.getLogger(__name__)


class FolderCleaner:
    """Removes emptied folders deepest first, each change journaled."""

    def __init__(self, changes: JournaledChanges, tally: Tally) -> None:
        """Prepare the removals of a run.

        Args:
            changes: The journaled changes of the run (same sequence as its moves).
            tally: Counters of the run: failures are recorded there.
        """
        self._changes = changes
        self._tally = tally

    def run(self, folders: list[Path], rules: FolderRules) -> FolderReport:
        """Remove every candidate left empty but for junk.

        Args:
            folders: The candidates, deepest first.
            rules: Junk files, and whether they can be set aside.

        Returns:
            How many folders were removed, and those left.
        """
        return FolderReport.of(self._act(verdicts(folders, rules)))

    def _act(self, found: Iterator[Verdict]) -> Iterator[Verdict]:
        """Remove each folder found empty, before the walk looks at its parent.

        Args:
            found: The verdicts, read from the disk one by one.

        Yields:
            What happened to each folder.
        """
        for verdict in found:
            if verdict.fate is not Fate.REMOVED:
                yield verdict
                continue
            try:
                for junk in verdict.junk:
                    self._changes.quarantine(file_of(junk), ActionKind.QUARANTINE_JUNK)
                entry = self._changes.entry(
                    file_of(verdict.folder, (0, 0)), ActionKind.REMOVE_FOLDER
                )
                self._changes.record(entry, verdict.folder.rmdir)
            except OSError as exc:
                _LOGGER.debug("Removal failed on %s", verdict.folder, exc_info=True)
                reason = exc.strerror or str(exc)
                self._tally.failed.append(Incident(verdict.folder, reason))
                yield Verdict(verdict.folder, Fate.HOLDS_FILES)
                continue
            yield verdict
