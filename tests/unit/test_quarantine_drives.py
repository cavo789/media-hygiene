"""One quarantine per drive (0183): the drives' mounts, the runs, `mh`'s mounts."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.actions.purge import run_folders, runs_in
from media_hygiene.paths.docker_run import Shell, Volume
from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.paths.quarantines import Quarantines, is_drive_folder
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_drives import with_drive_quarantines
from media_hygiene.services.launcher_folders import FolderChoice, with_folders
from media_hygiene.services.next_command import NextVerb, next_command
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.services.launcher import LauncherScript
    from media_hygiene.services.runtime import Runtime

_Q: Final = Path("/quarantine")
_COMMANDS: Final = LauncherCommands(("clean",), ("clean",), (), (), 9000)


def _runtime(table: MountTable | None = None) -> Runtime:
    """Every mount point where the image expects it; `table` the mounts."""
    locations = Locations.model_validate(
        {f"{kind.value}_dir": Path(f"/{kind.value}") for kind in MountKind}
    )
    return replace(make_runtime(locations), mounts=table or MountTable(frozenset()))


def _script(*photos: str, quarantine: str | None = None) -> LauncherScript:
    """The script of `launcher --photos … [--quarantine …]`, drives added."""
    runtime = _runtime()
    choice = FolderChoice(photos, quarantine)
    built = launcher_script(runtime, choice.shell(), _COMMANDS)
    return with_drive_quarantines(with_folders(runtime, built, choice))


@pytest.mark.parametrize(
    ("name", "drive"),
    [("e", True), ("z", True), ("E", False), ("ee", False), ("20260925-183015", False)],
)
def test_only_one_lowercase_letter_names_a_drive(
    name: str,
    drive: bool,  # noqa: FBT001
) -> None:
    """A run identifier never looks like a drive's folder."""
    assert is_drive_folder(name) is drive


def test_the_drives_are_the_one_letter_mounts_below_the_quarantine() -> None:
    """/quarantine/e is E:'s; deeper, other names or elsewhere: not a drive's."""
    points = {_Q, _Q / "e", _Q / "d", _Q / "e" / "x", _Q / "ab", Path("/data/f")}
    quarantines = Quarantines.mounted(_Q, points)
    assert quarantines.by_drive == (("D:", _Q / "d"), ("E:", _Q / "e"))
    assert quarantines.folders == (_Q, _Q / "d", _Q / "e")


def test_a_file_of_an_unmounted_drive_quarantine_names_the_drive() -> None:
    """Only a file below /quarantine/<letter>/<run> whose mount is gone."""
    quarantines = Quarantines.mounted(_Q, {_Q / "e"})
    assert quarantines.unplugged("/quarantine/d/20260925-183015/d/a.jpg") == "D:"
    assert quarantines.unplugged("/quarantine/e/20260925-183015/e/a.jpg") is None
    assert quarantines.unplugged("/quarantine/20260925-183015/d/a.jpg") is None
    assert quarantines.unplugged("/elsewhere/d/20260925-183015/a.jpg") is None


def test_runs_are_read_in_every_quarantine_never_the_drive_folders(
    tmp_path: Path,
) -> None:
    """A run on two drives is listed once; the `e` folder Docker made is no run."""
    default, own = tmp_path, tmp_path / "e"
    for folder in (default / "20260101-000000", own / "20260101-000000"):
        folder.mkdir(parents=True)
    (own / "20260202-000000").mkdir()
    assert runs_in((default, own)) == ["20260202-000000", "20260101-000000"]
    assert run_folders((default, own), "20260101-000000") == [
        default / "20260101-000000",
        own / "20260101-000000",
    ]
    assert run_folders((default, own), "e") == []


def test_each_photo_drive_but_c_gets_its_quarantine_created_by_mh() -> None:
    """E: and D: get one each, mounted and created; C: keeps /quarantine."""
    script = _script("C:\\Photos", "E:\\Photos", "e:\\Videos", "D:\\Images")
    assert script.drives == (
        Volume("D:\\media-hygiene\\quarantine", _Q / "d"),
        Volume("E:\\media-hygiene\\quarantine", _Q / "e"),
    )
    assert script.created[-2:] == (
        "D:\\media-hygiene\\quarantine",
        "E:\\media-hygiene\\quarantine",
    )
    assert with_drive_quarantines(script) == script
    text = render_script(script)
    assert '-v "E:\\media-hygiene\\quarantine:/quarantine/e" `' in text
    assert '"E:\\media-hygiene\\quarantine"' in text  # New-Item, `mh folders`
    assert "/quarantine/c" not in text


def test_a_whole_drive_given_as_photos_gets_its_own_quarantine() -> None:
    r"""E:\ itself: its quarantine on /quarantine/e, never read by the audit (0192)."""
    script = _script("C:\\Photos", "E:\\")
    assert script.drives == (Volume("E:\\media-hygiene\\quarantine", _Q / "e"),)


def test_a_quarantine_the_user_named_receives_every_drive() -> None:
    r"""--quarantine D:\Q: no drive quarantine, C:'s photos included (0193)."""
    script = _script("C:\\Photos", "E:\\Photos", quarantine="D:\\Q")
    assert script.drives == ()
    text = render_script(script)
    assert "/quarantine/e" not in text
    assert "/quarantine/c" not in text
    assert not any("media-hygiene\\quarantine" in folder for folder in script.created)


def test_the_default_quarantine_keeps_one_per_drive() -> None:
    """Without --quarantine: E:'s own, as before (0183)."""
    assert _script("C:\\Photos", "E:\\Photos").drives == (
        Volume("E:\\media-hygiene\\quarantine", _Q / "e"),
    )


def test_wsl_folders_get_their_drive_quarantine_too() -> None:
    """/mnt/e/Photos: /mnt/e/media-hygiene/quarantine on /quarantine/e."""
    script = _script("/mnt/e/Photos", "/home/me/Pictures")
    assert script.shell is Shell.BASH
    assert script.drives == (Volume("/mnt/e/media-hygiene/quarantine", _Q / "e"),)
    assert '-v "/mnt/e/media-hygiene/quarantine:/quarantine/e" \\' in render_script(
        script
    )


def test_the_next_docker_run_keeps_the_drives_quarantines() -> None:
    """Without mh, the command printed after a clean mounts /quarantine/e again."""
    table = MountTable(
        frozenset({Path("/data/e/Photos"), _Q, _Q / "e"}),
        (
            (Path("/data/e/Photos"), "E:\\Photos"),
            (_Q, "C:\\q"),
            (_Q / "e", "E:\\media-hygiene\\quarantine"),
        ),
    )
    command = next_command(_runtime(table), NextVerb("undo")).command
    assert '-v "E:\\media-hygiene\\quarantine:/quarantine/e"' in command
