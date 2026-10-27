"""Where `purge --to` copied a run before erasing it: `<run>.archived.json` (0306).

Written next to the run's journal, beside `<run>.purged.json` (which the purge still
writes, so every reader of purged runs treats an archived run as purged). A record
that cannot be written never stops the purge; it is logged.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict

from media_hygiene.actions.purged import write_record

if TYPE_CHECKING:
    from pathlib import Path

_LOGGER = logging.getLogger(__name__)
ARCHIVED_SUFFIX: Final = ".archived.json"


class ArchiveRecord(BaseModel):
    """The run copied before its purge, when (UTC) and where."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1] = 1
    run: str
    archived: datetime
    target: str


def note_archived(journal_dir: Path, record: ArchiveRecord) -> None:
    """Write the archive record of a run, whole or not at all.

    Args:
        journal_dir: Journal mount point.
        record: What to record.
    """
    target = journal_dir / f"{record.run}{ARCHIVED_SUFFIX}"
    try:
        write_record(target, record)
    except OSError as exc:
        _LOGGER.warning("Cannot record the archive of %s: %s", record.run, exc.strerror)


def archive_record(run: str, target: str) -> ArchiveRecord:
    """Build the record of a run archived now.

    Args:
        run: The run.
        target: Where it was copied.

    Returns:
        The record.
    """
    return ArchiveRecord(run=run, archived=datetime.now(UTC), target=target)
