"""The `mh` launcher script: the mounts of one run, the mode chosen per command."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.host_folders import HostFolder
from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_file import load_command
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest

    from media_hygiene.services.runtime import Runtime

_PHOTOS = Path("/data/c/Photos")
_COMMANDS = LauncherCommands(
    names=("audit", "clean", "review", "launcher"),
    writers=("clean",),
    pages=("review",),
    data=("launcher",),
    port=8088,
)


def _runtime() -> Runtime:
    r"""An audit of `C:\Photos` with its reports folder and the cache volume.

    Returns:
        The runtime.
    """
    locations = Locations.model_validate(
        {f"{kind.value}_dir": Path(f"/{kind.value}") for kind in MountKind}
    )
    cache = HostFolder(
        "dev:8:1", ("/", "var", "lib", "docker", "volumes", "my-cache", "_data")
    )
    table = MountTable(
        frozenset({_PHOTOS, Path("/reports"), Path("/cache")}),
        ((_PHOTOS, "C:\\Photos"), (Path("/reports"), "D:\\reports")),
        ((Path("/cache"), cache),),
    )
    return replace(make_runtime(locations), mounts=table)


def test_powershell_keeps_the_folders_and_defaults_the_missing_ones(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Guessed PowerShell; :ro chosen per command; tool folders kept or in the home."""
    monkeypatch.setenv("TZ", "Europe/Brussels")
    monkeypatch.setenv("MEDIA_HYGIENE_LAUNCHER", "1")
    script = launcher_script(_runtime(), None, _COMMANDS)
    assert script.shell is Shell.POWERSHELL
    text = render_script(script)
    assert text.startswith("# media-hygiene launcher")
    assert '. "$HOME\\media-hygiene\\mh.ps1"' in text
    assert "function global:mh {" in text
    assert "$mode = if ($command -in @('clean')) { '' } else { ':ro' }" in text
    assert (
        "@('-p', '127.0.0.1:8088:8088', '-e', 'MEDIA_HYGIENE_REVIEW__PORT=8088')"
        in text
    )
    assert "$tty = @(if ($command -notin @('launcher')) { '-it' })" in text
    assert "docker run --rm @tty `" in text
    assert "'-v'; \"C:\\Photos:/data/c/Photos${mode}\" }" in text
    assert '-v "D:\\reports:/reports" `' in text
    assert '-v "my-cache:/cache" `' in text
    assert '-v "$HOME\\media-hygiene\\journal:/journal" `' in text
    assert '"$HOME\\media-hygiene\\config", "$HOME\\media-hygiene\\journal"' in text
    assert '-e "TZ=Europe/Brussels" `' in text
    assert "MEDIA_HYGIENE_LAUNCHER=1" not in text  # its own shell, never carried
    assert (
        "            cavo789/media-hygiene @rest @backups @($nas.backups)\n"
        "        $status = $LASTEXITCODE" in text
    )


def test_bash_creates_the_home_folders_and_runs_as_the_user() -> None:
    """Asked for bash: mkdir -p, --user, the cache volume named like the README."""
    runtime = replace(_runtime(), mounts=MountTable(frozenset()))
    text = render_script(launcher_script(runtime, Shell.BASH, _COMMANDS))
    assert "mh() {" in text
    assert 'mkdir -p "$HOME/media-hygiene/config" "$HOME/media-hygiene/reports"' in text
    assert '--user "$(id -u):$(id -g)"' in text
    assert '-v "media-hygiene-cache:/cache" \\' in text
    assert 'case " clean " in' in text
    assert 'source "$HOME/media-hygiene/mh.sh"' in text
    assert load_command(Shell.BASH) == 'source "$HOME/media-hygiene/mh.sh"'


def test_a_folder_not_found_ends_powershell_with_2() -> None:
    """Measured 2026-10-20 (15e): said, but exit code 0; now 2, as mh.sh says it."""
    text = render_script(launcher_script(_runtime(), Shell.POWERSHELL, _COMMANDS))
    missing = [line for line in text.splitlines() if "or write mh again" in line]
    # a --photos folder, the folder of `import <folder>` (0378), the launcher line's
    assert len(missing) == 3
    assert all("$global:LASTEXITCODE = 2; return" in line for line in missing)
