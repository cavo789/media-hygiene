"""`mh share` (0296): one fixed folder, mounted for this command only, opened after."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import replace
from typing import TYPE_CHECKING, Final

from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

_COMMANDS: Final = LauncherCommands(
    names=("audit", "share", "backup", "restore"),
    writers=(),
    pages=(),
    data=(),
    port=8088,
)
# `docker` stands in for the image: it prints the arguments it was given, one per line.
_FAKE_DOCKER: Final = "docker() { printf 'ran:%s\\n' \"$@\"; }"


def _script(tmp_path: Path, shell: Shell) -> str:
    """The `mh` of a run without any mount."""
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    return render_script(launcher_script(runtime, shell, _COMMANDS))


def _bash(tmp_path: Path, command: str) -> list[str]:
    """Load the bash `mh`, run a command; the arguments `docker` received."""
    script = tmp_path / "mh.sh"
    script.write_text(_script(tmp_path, Shell.BASH))
    bash = shutil.which("bash") or "bash"
    # Trusted script written by the test itself, run on its temporary folder.
    done = subprocess.run(  # noqa: S603
        [bash, "-c", f"{_FAKE_DOCKER}\nsource {script}; mh {command}"],
        capture_output=True,
        text=True,
        check=False,
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"},
    )
    return [line.removeprefix("ran:") for line in done.stdout.splitlines()]


def test_bash_mounts_the_shares_folder_for_share_only(tmp_path: Path) -> None:
    """`mh share`: the folder made and mounted on /shares; `mh audit`: not."""
    ran = _bash(tmp_path, 'share --album "Crete 2023"')
    shares = tmp_path / "media-hygiene" / "Shares"
    assert f"{shares}:/shares" in ran
    assert shares.is_dir()
    assert ran[-2:] == ["--album", "Crete 2023"]
    assert not any(line.endswith(":/shares") for line in _bash(tmp_path, "audit"))


def test_powershell_mounts_it_for_share_then_opens_it(tmp_path: Path) -> None:
    """The mount and the Explorer, for `share` only, never after its help."""
    text = _script(tmp_path, Shell.POWERSHELL)
    assert "if ($command -eq 'share') {" in text
    assert "$share = @('-v', \"$HOME\\media-hygiene\\Shares:/shares\")" in text
    assert "            @share `" in text
    assert "@('--help', '-h')" in text
    assert 'Invoke-Item -LiteralPath "$HOME\\media-hygiene\\Shares"' in text


def test_powershell_copies_the_archives_off_the_pc(tmp_path: Path) -> None:
    """backup/restore (0414, 0419): --to/--from, else the push target, guarded."""
    text = _script(tmp_path, Shell.POWERSHELL)
    assert "$keep = _mh_keep_before $command $rest" in text
    assert "$rest = @($keep.rest)" in text
    assert "if ($keep -and $status -eq 0) { _mh_keep_after $keep }" in text
    # The default: the folder .mh-backups of the push target, read from its file.
    assert "_mh_nas_file 'push-target.txt'" in text
    assert '$other = "$pushed\\.mh-backups"' in text
    # Unreachable: said, the PC copy kept; typed with --to/--from: the command stops.
    assert "if ($typed) { $global:LASTEXITCODE = 2; return $null }" in text
    # Another mh container: refused, but the home page waiting for this step.
    assert 'docker ps -q --filter "ancestor=' in text
    # A copy is whole or absent: written under .part, its size checked, then renamed.
    assert '$draft = "$there.part"' in text
    assert "if ((Get-Item -LiteralPath $draft).Length -ne $file.Length)" in text
    # Only archives are removed there, and only once every archive of the PC is in.
    assert "-Filter 'mh-backup-*.zip'" in text
    assert "$home" not in text.replace("$HOME", "")


def test_bash_keeps_the_pc_folder(tmp_path: Path) -> None:
    """The bash `mh` has no push target: the archives stay in the PC folder."""
    ran = _bash(tmp_path, "backup")
    assert f"{tmp_path / 'media-hygiene' / 'backups'}:/backups" in ran
