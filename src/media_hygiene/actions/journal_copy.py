"""A copy of each run's journal beside its quarantine folder (0697).

`/quarantine/<run>.jsonl` (and `/quarantine/<x>/<run>.jsonl` on a drive's own
quarantine) travels with the files the run set aside: lose `/journal` and `undo`
still knows where each file came from. It lies **beside** the run's folder, never in
it, so no reader of a run folder takes it for a file set aside, and no reader of the
quarantine takes it for a run (a run is a folder). Written atomically (a temporary
name, then a rename), read back byte for byte; `purge <run>` erases it with the run.
"""

from __future__ import annotations

import contextlib
import errno
import os
from typing import TYPE_CHECKING

from media_hygiene.actions.runs import RUN_ID_PATTERN
from media_hygiene.constants import JOURNAL_SUFFIX

if TYPE_CHECKING:
    from pathlib import Path


def journal_copy(quarantine_dir: Path, run_id: str) -> Path:
    """Where the copy of a run's journal lies in one quarantine.

    Args:
        quarantine_dir: A quarantine (the default one, or a drive's).
        run_id: The run.

    Returns:
        `<quarantine_dir>/<run_id>.jsonl`, beside the run's folder.
    """
    return quarantine_dir / f"{run_id}{JOURNAL_SUFFIX}"


def write_copy(source: Path, target: Path) -> None:
    """Copy a journal atomically, then prove the copy by reading it back.

    Args:
        source: The journal copied (`/journal/<run>.jsonl`, or its copy).
        target: Where the copy goes.

    Raises:
        OSError: The copy could not be written, or does not read back the same
            (a former copy stays as it was).
    """
    content = source.read_bytes()
    draft = target.with_name(f".{target.name}.tmp")
    try:
        with draft.open("wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        draft.replace(target)
    finally:
        with contextlib.suppress(OSError):
            draft.unlink(missing_ok=True)
    if target.read_bytes() != content:
        raise OSError(errno.EIO, os.strerror(errno.EIO), str(target))  # not as written


def remove_copy(quarantine_dir: Path, run_id: str) -> None:
    """Erase the copy of a run's journal from one quarantine, if there is one.

    Args:
        quarantine_dir: A quarantine.
        run_id: The run.
    """
    copy = journal_copy(quarantine_dir, run_id)
    if copy.is_file() and not copy.is_symlink():
        copy.unlink()


def found_copy(quarantines: tuple[Path, ...], run_id: str) -> Path | None:
    """Find a copy of a run's journal in the quarantines.

    Args:
        quarantines: The default quarantine and the per-drive ones.
        run_id: The run.

    Returns:
        The first copy found, the default quarantine first; None without one.
    """
    copies = (journal_copy(folder, run_id) for folder in quarantines)
    return next((copy for copy in copies if copy.is_file()), None)


def copied_journals(quarantines: tuple[Path, ...]) -> dict[str, Path]:
    """Every copy of a run's journal in the quarantines that are there.

    A quarantine missing, or a drive's not mounted (Docker's empty folder for it is
    no mount, so not in `quarantines`), gives none: no run is invented.

    Args:
        quarantines: The default quarantine and the per-drive ones.

    Returns:
        Each run's first copy, the default quarantine first.
    """
    copies: dict[str, Path] = {}
    for folder in quarantines:
        if not folder.is_dir():
            continue
        for copy in sorted(folder.glob(f"*{JOURNAL_SUFFIX}")):
            run_id = copy.name.removesuffix(JOURNAL_SUFFIX)
            if RUN_ID_PATTERN.fullmatch(run_id) and copy.is_file():
                copies.setdefault(run_id, copy)
    return copies
