"""A journaled run context in a temporary folder, for the executors' tests."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalEntry, JournalWriter
from media_hygiene.actions.journaled import CleanContext
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.scan.progress import NullProgress

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

JOURNAL_NAME = "run.jsonl"


def move(seq: int, row: str, paths: tuple[Path, Path]) -> JournalEntry:
    """A pending move of plan `p`, from `paths[0]` to `paths[1]`."""
    return JournalEntry(
        seq=seq,
        phase=Phase.SORT,
        status=Status.PENDING,
        action=ActionKind.MOVE,
        path=str(paths[0]),
        host_path=str(paths[0]),
        size=1,
        mtime_ns=0,
        target=str(paths[1]),
        plan="p",
        row=row,
    )


@contextmanager
def journaled(
    tmp_path: Path, phase: Phase = Phase.CLEAN, *, delete: bool = False
) -> Iterator[CleanContext]:
    """Open `run.jsonl` under `tmp_path`; the quarantine is `tmp_path/quarantine`.

    Args:
        tmp_path: The test's folder, also the root of the host paths.
        phase: The command of the run.
        delete: `clean --delete`.

    Yields:
        The context of the run.
    """
    with JournalWriter.open(tmp_path / JOURNAL_NAME) as journal:
        yield CleanContext(
            journal,
            HostPathMapper(tmp_path),
            tmp_path / "quarantine",
            NullProgress(),
            phase,
            delete_copies=delete,
        )
