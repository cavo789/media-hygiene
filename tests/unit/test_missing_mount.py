"""A missing tool folder comes with the whole command to paste, not a template."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.missing_mount import missing_mount
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
