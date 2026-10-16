"""Permanently delete the quarantine of one or every run.

Only the folders the tool made are ever deleted: a direct child of the quarantine
named like a run (`20260925-183015`), a real folder (not a link to one elsewhere).
Anything else found there is left alone, the drives' folders (`/quarantine/e`, a
quarantine of its own) included: a run's quarantine may lie in several of them.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from media_hygiene.actions.runs import RUN_ID_PATTERN
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


def quarantine_runs(quarantine_dir: Path) -> list[str]:
    """List the runs that still have quarantined files, newest first.

    Args:
        quarantine_dir: Quarantine mount point.

    Returns:
        The run identifiers.
    """
    if not quarantine_dir.is_dir():
        return []
    return sorted(
        (path.name for path in quarantine_dir.iterdir() if _is_run_folder(path)),
        reverse=True,
    )


def runs_in(quarantines: Sequence[Path]) -> list[str]:
    """List the runs that still have files in any of the quarantines, newest first.

    Args:
        quarantines: The default quarantine and the per-drive ones.

    Returns:
        The run identifiers, each once.
    """
    runs = {run for folder in quarantines for run in quarantine_runs(folder)}
    return sorted(runs, reverse=True)


def run_folders(quarantines: Sequence[Path], run_id: str) -> list[Path]:
    """Find the folders of a run in the quarantines.

    Args:
        quarantines: The default quarantine and the per-drive ones.
        run_id: The run.

    Returns:
        Its folder in each quarantine that has one.
    """
    folders = (folder / run_id for folder in quarantines)
    return [folder for folder in folders if _is_run_folder(folder)]


def _is_run_folder(path: Path) -> bool:
    """Tell whether a folder of the quarantine is the quarantine of a run.

    Args:
        path: A direct child of the quarantine.

    Returns:
        True for a real folder named like a run identifier.
    """
    return (
        RUN_ID_PATTERN.fullmatch(path.name) is not None
        and path.is_dir()
        and not path.is_symlink()
    )


def folder_size(folder: Path) -> int:
    """Sum the size of every file below `folder`.

    Args:
        folder: Folder to measure.

    Returns:
        Its size in bytes.
    """
    return sum(path.stat().st_size for path in folder.rglob("*") if path.is_file())


def file_count(folder: Path) -> int:
    """Count the files below `folder`.

    Args:
        folder: Folder to count.

    Returns:
        How many files it holds.
    """
    return sum(1 for path in folder.rglob("*") if path.is_file())


def purge_run(quarantine_dir: Path, run_id: str) -> int:
    """Delete the quarantined files of a run.

    Args:
        quarantine_dir: Quarantine mount point.
        run_id: Run whose quarantine goes.

    Returns:
        Bytes freed.

    Raises:
        OSError: The folder is not the quarantine of a run (nothing is deleted).
    """
    folder = quarantine_dir / run_id
    if not _is_run_folder(folder):
        raise OSError(_("{path} is not the quarantine of a run").format(path=folder))
    freed = folder_size(folder)
    shutil.rmtree(folder)
    return freed
