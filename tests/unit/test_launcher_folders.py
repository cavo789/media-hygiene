r"""`launcher --photos "C:\Photos"`: Windows paths, checked by `mh`, its zone (0173)."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from media_hygiene.cli.app import build_app
from media_hygiene.config.windows_zones import WINDOWS_ZONE_VARIABLE, iana_zone
from media_hygiene.config.zone import apply_timezone
from media_hygiene.errors import MountError
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_folders import (
    FolderChoice,
    container_point,
    with_folders,
)
from tests.support.runtime import make_runtime
from tests.unit.test_launcher_ascii import expanded

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.services.runtime import Runtime

_DATA: Final = Path("/data")
_COMMANDS: Final = LauncherCommands(
    names=("audit", "clean", "launcher"),
    writers=("clean",),
    pages=(),
    data=("launcher",),
    port=8088,
)
# `docker` stands in for the image: it prints the arguments it was given, one per line.
_FAKE_DOCKER: Final = "docker() { printf 'ran:%s\\n' \"$@\"; }"


def _runtime() -> Runtime:
    """A run with every mount point at its usual place and nothing mounted.

    Returns:
        The runtime.
    """
    locations = Locations.model_validate(
        {f"{kind.value}_dir": Path(f"/{kind.value}") for kind in MountKind}
    )
    return replace(make_runtime(locations), mounts=MountTable(frozenset()))


@pytest.mark.parametrize(
    ("host", "point"),
    [
        ("C:\\Photos", "/data/c/Photos"),
        ("c:/Photos/Été 2019/", "/data/c/Photos/Été 2019"),
        ("D:\\", "/data/d"),
        ("/mnt/c/Photos", "/data/c/Photos"),
        ("/mnt/e", "/data/e"),
        ("/home/me/Pictures", "/data/home/me/Pictures"),
    ],
)
def test_a_folder_gets_the_mount_point_of_the_whole_tool(host: str, point: str) -> None:
    """The convention of `host_paths`, WSL drives included."""
    assert container_point(_DATA, host) == Path(point)


@pytest.mark.parametrize(
    ("host", "said"),
    [("\\\\NAS\\photos", "network"), ("Photos", "full path")],
)
def test_network_and_relative_folders_are_refused(host: str, said: str) -> None:
    """No mount point to give them: one sentence says why."""
    with pytest.raises(MountError, match=said):
        container_point(_DATA, host)


def test_several_folders_and_the_quarantine_replace_the_defaults() -> None:
    """Each --photos a volume; --quarantine replaces the home folder, not created."""
    runtime = _runtime()
    choice = FolderChoice(("C:\\Photos", "D:\\Images\\Famille", "C:\\Photos"), "D:\\q")
    script = with_folders(
        runtime, launcher_script(runtime, choice.shell(), _COMMANDS), choice
    )
    assert script.shell is Shell.POWERSHELL
    assert [volume.host for volume in script.data] == [
        "C:\\Photos",
        "D:\\Images\\Famille",
    ]
    text = render_script(script)
    assert '-v "C:\\Photos:/data/c/Photos${mode}" `' in text
    assert '-v "D:\\Images\\Famille:/data/d/Images/Famille${mode}" `' in text
    assert '-v "D:\\q:/quarantine" `' in text
    assert "$HOME\\media-hygiene\\quarantine" not in text
    # The quarantine is on D: now: C: gets its own (0183), D: none.
    assert '-v "C:\\media-hygiene\\quarantine:/quarantine/c" `' in text
    assert "/quarantine/d" not in text
    assert 'foreach ($folder in @("C:\\Photos", "D:\\Images\\Famille")) {' in text
    assert '-e "MEDIA_HYGIENE_WINDOWS_ZONE=$((Get-TimeZone).Id)" `' in text


def test_a_folder_inside_another_is_refused_whatever_its_case() -> None:
    r"""C:\photos\2019 inside C:\Photos: each file would be its own duplicate."""
    runtime = _runtime()
    choice = FolderChoice(("C:\\Photos", "c:\\photos\\2019"))
    script = launcher_script(runtime, Shell.POWERSHELL, _COMMANDS)
    with pytest.raises(MountError, match="inside"):
        with_folders(runtime, script, choice)


def test_the_powershell_translation_is_written_in_ascii() -> None:
    r"""`mh --photos`: Resolve-Path, drive letter in lower case, `\` → `/`."""
    runtime = _runtime()
    choice = FolderChoice(("C:\\Photos\\Vidéos",))
    text = render_script(
        with_folders(
            runtime, launcher_script(runtime, choice.shell(), _COMMANDS), choice
        )
    )
    assert text.isascii()
    assert "Vid$([char]0x00E9)os" in text
    assert (
        '$given += "${full}:/data/" + $full.Substring(0, 1).ToLower() + '
        "($full.Substring(2) -replace '\\\\', '/')"
    ) in text
    assert '-v "C:\\Photos\\Vidéos:/data/c/Photos/Vidéos${mode}" `' in expanded(text)


def test_launcher_writes_a_stopping_script_for_a_refused_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`> mh.ps1` gets a script that stops with the reason, not an empty file."""
    monkeypatch.setenv("MEDIA_HYGIENE_CONFIG_DIR", str(tmp_path))
    result = CliRunner().invoke(
        build_app(), ["launcher", "--photos", "C:\\Photos", "--photos", "C:\\Photos\\X"]
    )
    assert result.exit_code == 1
    assert result.stdout.startswith("# C:\\Photos\\X is inside C:\\Photos")
    assert "throw (" in result.stdout
    assert "inside C:\\Photos" in result.stderr


def test_launcher_takes_photos_without_any_mount(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No -v at all: the folders typed are the script's, the shell guessed."""
    monkeypatch.setenv("MEDIA_HYGIENE_CONFIG_DIR", str(tmp_path))
    result = CliRunner().invoke(build_app(), ["launcher", "--photos", "C:\\Photos"])
    assert result.exit_code == 0, result.output
    assert "function global:mh {" in result.stdout
    assert '-v "C:\\Photos:/data/c/Photos${mode}" `' in result.stdout
    assert "No photo folder" not in result.stderr


def _bash(tmp_path: Path, choice: FolderChoice, line: str) -> str:
    """Write the bash `mh` of these folders, then run `line` with a fake `docker`.

    Args:
        tmp_path: The test's folder, for the script and the home.
        choice: The folders of the launcher run.
        line: The bash commands, after loading the script.

    Returns:
        Everything printed, both streams.
    """
    runtime = _runtime()
    script = tmp_path / "mh.sh"
    built = with_folders(
        runtime, launcher_script(runtime, Shell.BASH, _COMMANDS), choice
    )
    script.write_text(render_script(built))
    bash = shutil.which("bash") or "bash"
    environment = {
        "HOME": str(tmp_path),
        "PATH": os.environ["PATH"],
        "TZ": "Asia/Tokyo",
    }
    # Trusted script written by the test itself, run on its temporary folder.
    done = subprocess.run(  # noqa: S603
        [bash, "-c", f"{_FAKE_DOCKER}\nsource {script}; {line}; echo status=$?"],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    return done.stdout + done.stderr


def test_bash_translates_photos_as_python_does(tmp_path: Path) -> None:
    """`mh --photos <folder> audit`: the same mount point as `launcher --photos`."""
    photos, key = tmp_path / "photos", tmp_path / "key"
    photos.mkdir()
    key.mkdir()
    shown = _bash(tmp_path, FolderChoice((str(photos),)), f"mh --photos {key} audit")
    point = container_point(_DATA, str(key)).as_posix()
    assert f"ran:{key}:{point}:ro" in shown
    assert f"ran:{photos}:{container_point(_DATA, str(photos)).as_posix()}:ro" in shown
    assert "ran:--photos" not in shown
    assert "ran:TZ=Asia/Tokyo" in shown
    assert "status=0" in shown


def test_bash_stops_on_a_folder_not_found(tmp_path: Path) -> None:
    """A disk not plugged in: said, docker never runs, status 2."""
    gone = tmp_path / "gone"
    shown = _bash(tmp_path, FolderChoice((str(gone),)), "mh audit")
    assert f"{gone} cannot be found" in shown
    assert "ran:" not in shown
    assert "status=2" in shown


@pytest.fixture
def process_zone() -> Iterator[None]:
    """Give the process zone back after the test, whatever it set."""
    saved = os.environ.get("TZ")
    yield
    if saved is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = saved
    time.tzset()


def test_a_windows_zone_id_gets_its_iana_name() -> None:
    """The CLDR table, with the current names of the old links."""
    assert iana_zone("Romance Standard Time") == "Europe/Paris"
    assert iana_zone("FLE Standard Time") == "Europe/Kyiv"
    assert iana_zone("India Standard Time") == "Asia/Kolkata"
    assert not iana_zone("Nowhere Standard Time")
    assert not iana_zone("")


@pytest.mark.usefixtures("process_zone")
def test_the_windows_zone_applies_when_nothing_else_says_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Precedence: [general] timezone > TZ > the zone of the Windows host."""
    monkeypatch.setenv(WINDOWS_ZONE_VARIABLE, "Tokyo Standard Time")
    monkeypatch.delenv("TZ", raising=False)
    apply_timezone("")
    assert os.environ["TZ"] == "Asia/Tokyo"
    monkeypatch.setenv("TZ", "Europe/Brussels")
    apply_timezone("")
    assert os.environ["TZ"] == "Europe/Brussels"
    apply_timezone("America/Montreal")
    assert os.environ["TZ"] == "America/Montreal"
