"""A folder on a drive Docker Desktop cannot see stops the commands reading it."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from media_hygiene.errors import MountError
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.data_checks import refuse_empty_data
from media_hygiene.services.unseen_drives import refuse_unseen_drives, share_command
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


def _runtime(tmp_path: Path, *unseen: tuple[Path, str]) -> Runtime:
    """A runtime with one photo folder and the given unseen drives.

    Args:
        tmp_path: Temporary directory.
        *unseen: (mount point, Windows folder) pairs.

    Returns:
        The runtime.
    """
    runtime = make_runtime(make_locations(tmp_path))
    (runtime.locations.data_dir / "d" / "backup").mkdir(parents=True)
    return replace(runtime, mounts=MountTable(frozenset(), unseen_drives=unseen))


def test_nothing_unseen_lets_the_command_run(tmp_path: Path) -> None:
    """Without such a drive, nothing is refused."""
    refuse_unseen_drives(_runtime(tmp_path))


def test_an_unseen_backup_stops_the_audit(tmp_path: Path) -> None:
    """The folder is named, and the tip says how to share its drive."""
    point = tmp_path / "data" / "d" / "backup"
    runtime = _runtime(tmp_path, (point, "D:\\backup"))
    with pytest.raises(MountError) as error:
        refuse_empty_data(runtime, "audit")
    assert "D:\\backup" in error.value.message
    assert error.value.tip is not None
    assert share_command("D") in error.value.tip


def test_two_unseen_folders_are_both_named(tmp_path: Path) -> None:
    """Every folder is named, `clean` and `undo` alike are refused."""
    runtime = _runtime(
        tmp_path,
        (tmp_path / "a", "D:\\backup"),
        (tmp_path / "b", "E:\\Photos"),
    )
    for command in ("clean", "undo"):
        with pytest.raises(MountError, match=r"D:\\backup, E:\\Photos"):
            ensure_can_act(runtime, command)


def test_share_command_mounts_the_drive_as_mh_does() -> None:
    """The command is the one measured to work (0252)."""
    assert share_command("E") == (
        'wsl -d docker-desktop sh -c "mkdir -p /mnt/host/e && '
        'mount -t drvfs E: /mnt/host/e"'
    )
