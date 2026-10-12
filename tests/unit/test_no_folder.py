"""A run without any photo folder offers the command that mounts the guide's folder."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.paths.host_folders import HostFolder
from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.missing_mount import no_folder
from media_hygiene.services.next_command import LAUNCHER_VARIABLE
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest

_LOCATIONS = Locations.model_validate(
    {"data_dir": Path("/data"), "cache_dir": Path("/cache")}
)
_CACHE = Path("/cache")


def test_without_any_mount_powershell_and_the_guide() -> None:
    r"""Nothing mounted: `C:\Photos` read-only, how to check it exists, the guide."""
    runtime = replace(make_runtime(_LOCATIONS), mounts=MountTable(frozenset(), (), ()))
    error = no_folder(runtime, "audit")
    assert error.message == "No folder to analyse under /data."
    assert error.tip is not None
    assert 'Test-Path "C:\\Photos"' in error.tip
    assert error.command is not None
    assert error.command.startswith("docker run --rm -it `")
    assert '"C:\\Photos:/data/c/Photos:ro"' in error.command
    assert error.command.rstrip().endswith("audit")
    assert error.link is not None
    assert error.link[1].endswith("/start/01-first-audit/")


def test_linux_tool_folders_give_a_bash_command() -> None:
    """A cache mounted from a Linux folder: the command is for bash, kept mounts too."""
    host = HostFolder("dev:8:1", ("/", "home", "me", "cache"))
    table = MountTable(frozenset({_CACHE}), (), ((_CACHE, host),))
    runtime = replace(make_runtime(_LOCATIONS), mounts=table)
    error = no_folder(runtime, "classify")
    assert error.command is not None
    assert '"/mnt/c/Photos:/data/c/Photos:ro"' in error.command
    assert '"/home/me/cache:/cache"' in error.command
    assert error.tip is not None
    assert 'ls "/mnt/c/Photos"' in error.tip


def test_under_the_launcher_no_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """`mh` mounts the folders itself: no `docker run` to paste, the guide still."""
    monkeypatch.setenv(LAUNCHER_VARIABLE, "1")
    runtime = replace(make_runtime(_LOCATIONS), mounts=MountTable(frozenset(), (), ()))
    error = no_folder(runtime, "audit")
    assert error.command is None
    assert error.link is not None
