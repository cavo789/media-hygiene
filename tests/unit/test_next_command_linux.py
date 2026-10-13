"""Native Linux: the `-v` of the next command, whatever the partitions of the host."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from media_hygiene.paths.host_folders import HostFolder, bind_source
from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.next_command import NextVerb, next_command
from tests.support.runtime import make_runtime

_PHOTOS = Path("/data/home/me/Pictures")
_DISK = Path("/data/media/me/Disk")
_ELSEWHERE = Path("/data/pictures")


def _command(point: Path, root: tuple[str, ...]) -> str:
    """The next command of an audit of one folder, its mountinfo root given."""
    locations = Locations.model_validate(
        {f"{kind.value}_dir": Path(f"/{kind.value}") for kind in MountKind}
    )
    folder = HostFolder("dev:259:3", ("/", *root))
    table = MountTable(frozenset({point}), (), ((point, folder),))
    runtime = replace(make_runtime(locations), mounts=table)
    return next_command(runtime, NextVerb("review", port=8088)).command


@pytest.mark.parametrize(
    ("point", "root", "volume"),
    [
        (
            _PHOTOS,
            ("home", "me", "Pictures"),
            "/home/me/Pictures:/data/home/me/Pictures",
        ),
        (_PHOTOS, ("me", "Pictures"), "/home/me/Pictures:/data/home/me/Pictures"),
        (_DISK, (), "/media/me/Disk:/data/media/me/Disk"),
        (_ELSEWHERE, ("home", "me", "Pictures"), "/home/me/Pictures:/data/pictures"),
    ],
)
def test_the_volume_is_typed_again_as_the_user_wrote_it(
    point: Path, root: tuple[str, ...], volume: str
) -> None:
    """Root file system, `/home` or a USB disk of its own, a free mount point.

    Args:
        point: The mount point under /data.
        root: The folder of its file system the mount table shows.
        volume: The `-v` expected.
    """
    assert f'-v "{volume}:ro"' in _command(point, root)


def test_a_windows_folder_or_a_volume_is_kept_as_found() -> None:
    r"""Docker Desktop's `C:\Photos` and a named volume are never rewritten."""
    assert bind_source("C:\\Photos", "C:\\Photos") == "C:\\Photos"
    assert bind_source("media-hygiene-cache", "/x") == "media-hygiene-cache"
    assert bind_source(None, "/home/me/Pictures") == "/home/me/Pictures"
