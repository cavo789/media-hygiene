"""The closing line of `launcher`: what `mh` remembers, backups apart (0249)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.config.settings import Settings
from media_hygiene.paths.docker_run import Volume
from media_hygiene.services.launcher_memory import remembered

if TYPE_CHECKING:
    from media_hygiene.services.launcher import LauncherScript
    from media_hygiene.services.runtime import Runtime

_FOLDER = Volume("C:\\Photos", Path("/data/c/Photos"))
_BACKUP = Volume("E:\\Backup", Path("/data/e/Backup"))


def line(data: int, backups: int) -> str:
    """The line for some folders and some backups."""
    runtime = cast("Runtime", SimpleNamespace(settings=Settings()))
    script = cast(
        "LauncherScript",
        SimpleNamespace(data=(_FOLDER,) * data, backups=(_BACKUP,) * backups, nas=()),
    )
    return remembered(runtime, script)


@pytest.mark.parametrize(
    ("data", "backups", "said"),
    [
        (2, 0, "mh remembers: 2 folders, language en"),
        (1, 1, "mh remembers: 1 folder, 1 backup (read-only), language en"),
        (2, 2, "mh remembers: 2 folders, 2 backups (read-only), language en"),
    ],
)
def test_backups_are_counted_apart_and_only_when_there_are(
    data: int, backups: int, said: str
) -> None:
    """No backup: the line as before; else the count, read-only."""
    assert line(data, backups).startswith(said)
