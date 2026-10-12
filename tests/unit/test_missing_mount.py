"""A missing tool folder comes with the whole command to paste, not a template."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from media_hygiene.errors import MountError
from media_hygiene.paths.host_folders import HostFolder
from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.clean import CleanService
from media_hygiene.services.missing_mount import again_arguments, missing_mount
from media_hygiene.services.next_command import NextVerb
from tests.support.runtime import make_runtime

_PHOTOS = Path("/data/c/Photos")


def test_the_command_mounts_the_photos_again_and_adds_config() -> None:
    r"""`C:\Photos` read-only only: the command keeps it, adds /config and the port."""
    locations = Locations.model_validate(
        {f"{kind.value}_dir": Path(f"/{kind.value}") for kind in MountKind}
    )
    table = MountTable(frozenset({_PHOTOS}), ((_PHOTOS, "C:\\Photos"),), ())
    runtime = replace(make_runtime(locations), mounts=table)
    again = NextVerb("places", (MountKind.CONFIG,), port=4243)
    error = missing_mount(runtime, "No /config.", again)
    assert error.message == "No /config."
    assert error.tip is not None
    assert "/config" in error.tip
    assert error.command is not None
    assert error.command.startswith('mkdir -Force "$HOME\\media-hygiene\\config"')
    assert '"C:\\Photos:/data/c/Photos:ro"' in error.command
    assert '"$HOME\\media-hygiene\\config:/config"' in error.command
    assert "-p 127.0.0.1:4243:4243" in error.command
    assert error.command.rstrip().endswith("places")


def _clean_without_quarantine(table: MountTable, persistent: Path) -> MountError:
    """Run the checks of `clean` with only a journal and the photos mounted.

    Args:
        table: The mount table of the run.
        persistent: The test folder holding the journal.

    Returns:
        The error `clean` raises.
    """
    locations = Locations.model_validate({"journal_dir": persistent})
    runtime = replace(make_runtime(locations), mounts=table)
    with pytest.raises(MountError) as raised:
        CleanService(runtime, NullProgress()).ensure_ready()
    return raised.value


def test_clean_without_quarantine_powershell(tmp_path: Path) -> None:
    r"""`C:\Photos`: mkdir in the home, the photos writable, the quarantine added."""
    table = MountTable(frozenset({_PHOTOS}), ((_PHOTOS, "C:\\Photos"),), ())
    error = _clean_without_quarantine(table, tmp_path)
    assert error.command is not None
    assert error.command.startswith("mkdir -Force ")
    assert '"$HOME\\media-hygiene\\quarantine:/quarantine"' in error.command
    assert '"C:\\Photos:/data/c/Photos"' in error.command
    assert error.command.rstrip().endswith("clean")
    assert "--delete" not in f"{error.tip} {error.command}"


def test_clean_without_quarantine_bash(tmp_path: Path) -> None:
    """A Linux folder: `mkdir -p`, the same command for bash."""
    host = HostFolder("dev:8:1", ("/", "home", "me", "Photos"))
    table = MountTable(frozenset({_PHOTOS}), (), ((_PHOTOS, host),))
    error = _clean_without_quarantine(table, tmp_path)
    assert error.command is not None
    assert error.command.startswith("mkdir -p ")
    assert '"$HOME/media-hygiene/quarantine:/quarantine"' in error.command
    assert "--delete" not in f"{error.tip} {error.command}"


def test_the_typed_command_comes_back_quoted() -> None:
    """The user's own options are kept; a value with a space is quoted."""
    runtime = make_runtime(Locations())
    typed = ("--locale", "fr", "clean", "--prefer", "C:\\My photos")
    again = again_arguments(runtime, "clean", typed)
    assert again == '--locale fr clean --prefer "C:\\My photos"'
    assert again_arguments(runtime, "clean", ("-m", "pytest")) == "clean"
