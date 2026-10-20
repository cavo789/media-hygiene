"""When `purge` emptied the quarantine of a run: a record next to its journal (0256).

The journal of a run is never rewritten after it ends (write-ahead: `pending` then
`done`, read by `undo`, `history` and the journals' memory): the purge date goes to a
file of its own, `<run>.purged.json`, which no reader of journals lists (they read
`*.jsonl`). A run purged before this record existed has none: "purged since", undated.
A record that cannot be written never stops the purge (the files are gone already); one
that cannot be read is no date.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.actions.runs import RUN_ID_PATTERN

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

_LOGGER = logging.getLogger(__name__)
PURGED_SUFFIX: Final = ".purged.json"


class PurgeRecord(BaseModel):
    """The run whose quarantine `purge` erased, and when (UTC)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1] = 1
    run: str
    purged: datetime


def purge_record(journal_dir: Path, run_id: str) -> Path:
    """Name the purge record of a run, next to its journal.

    Args:
        journal_dir: Journal mount point.
        run_id: The run.

    Returns:
        The file.
    """
    return journal_dir / f"{run_id}{PURGED_SUFFIX}"


def note_purged(journal_dir: Path, run_id: str) -> None:
    """Record that the quarantine of a run was just erased.

    Written whole or not at all (a draft renamed); a failure is logged, never raised:
    the purge itself is done.

    Args:
        journal_dir: Journal mount point.
        run_id: The run purged.
    """
    record = PurgeRecord(run=run_id, purged=datetime.now(UTC))
    target = purge_record(journal_dir, run_id)
    draft = target.with_name(f".{target.name}.partial")
    try:
        draft.write_text(record.model_dump_json() + "\n", encoding="utf-8")
        draft.replace(target)
    except OSError as exc:
        _LOGGER.warning("Cannot record the purge of %s: %s", run_id, exc.strerror)


def purge_dates(journal_dir: Path, run_ids: Iterable[str]) -> Mapping[str, datetime]:
    """Read when each run's quarantine was purged, for the runs that recorded it.

    Args:
        journal_dir: Journal mount point.
        run_ids: The runs asked about.

    Returns:
        The purge date of each run that has a readable record; the others are left
        out (purged before 0256, or never purged).
    """
    dates: dict[str, datetime] = {}
    for run_id in run_ids:
        if RUN_ID_PATTERN.fullmatch(run_id) is None:
            continue  # a name from a plan line: never a path of its own
        try:
            text = purge_record(journal_dir, run_id).read_bytes()
            record = PurgeRecord.model_validate_json(text)
        except OSError, ValidationError:
            continue
        if record.run == run_id:
            dates[run_id] = record.purged
    return dates
