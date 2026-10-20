"""`mh.sh` in WSL: a drive WSL has not mounted (a USB stick) stops with a line to type.

TODO 0254, then 0259: WSL mounts the drives present when it starts; a stick plugged
in later is absent from `/mnt`. `mh.sh` never runs sudo: it says the `mount -t drvfs`
line to type, and the `umount` one for ejecting. Native Linux: nothing changes. Each
case runs the real bash functions with fake `mountpoint`, `cmd.exe`, `sudo`, `docker`.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.services.launcher import (
    LauncherCommands,
)
from media_hygiene.services.launcher_guards import launcher_guards
from media_hygiene.services.launcher_menu import menu_texts
from tests.support.host_bash import bash_mh, run_bash

if TYPE_CHECKING:
    import subprocess
    from pathlib import Path

    from media_hygiene.services.launcher_guards import WslTexts

_COMMANDS: Final = LauncherCommands(("audit", "review"), (), ("review",), (), 8088)
_FOLDER: Final = "/mnt/e/Photos"
# $MOUNTED: `mountpoint` says the drive is mounted; $WINDOWS: `cmd.exe /c vol` finds it
# (unset: no cmd.exe, native Linux). `sudo` only records a call: there must be none.
_FAKES: Final = r"""
mountpoint() { [[ -n "${MOUNTED:-}" ]]; }
if [[ -n "${WINDOWS+set}" ]]; then
    cmd.exe() { printf '%s\n' "$*" >> "$HOME/cmd"; [[ "$WINDOWS" == 1 ]]; }
fi
sudo() { printf '%s\n' "$*" >> "$HOME/sudo"; }
docker() { printf 'ran:%s\n' "$@"; }
"""


def _run(
    tmp_path: Path, line: str, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Load the bash `mh` with the fakes, then run `line` in `env`."""
    code = f"{bash_mh(tmp_path, _COMMANDS, _FAKES)}; {line}; echo status=$?"
    return run_bash(code, {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin", **env})


def _said(tmp_path: Path, name: str) -> list[str]:
    """The lines a fake program received, one per call."""
    path = tmp_path / name
    return path.read_text().splitlines() if path.exists() else []


def _texts() -> WslTexts:
    """The lines of the WSL drive, in English, `E` and `e` in place."""
    return launcher_guards().wsl


def _filled(text: str) -> str:
    """A line as bash prints it for drive E:."""
    return text.replace("${drive}", "E").replace("${letter}", "e")


def test_drive_absent_from_wsl_says_the_line_to_type(tmp_path: Path) -> None:
    """Windows has E:, WSL has not: the line and the command to type, nothing run."""
    with using(Locale.EN):
        texts = _texts()
        done = _run(tmp_path, f"mh audit --photos {_FOLDER}", {"WINDOWS": "1"})
    assert _filled(texts.unmounted) in done.stderr
    assert "sudo umount /mnt/e" in _filled(texts.unmounted)
    # Owned by the user, as WSL mounts its own drives: numbers, ready to paste.
    typed = re.compile(
        r"^    sudo mkdir -p /mnt/e && "
        r"sudo mount -t drvfs E: /mnt/e -o uid=\d+,gid=\d+$",
        re.MULTILINE,
    )
    assert typed.search(done.stderr)
    assert not _said(tmp_path, "sudo")
    assert "ran:" not in done.stdout
    assert "status=2" in done.stdout


def test_drive_already_mounted_is_left_alone(tmp_path: Path) -> None:
    """WSL has it (at its start, or by the line typed): nothing asked, nothing said."""
    done = _run(tmp_path, "_mh_drive /mnt/e/Photos", {"MOUNTED": "1", "WINDOWS": "1"})
    assert "status=0" in done.stdout
    assert not done.stderr
    assert not _said(tmp_path, "cmd")


@pytest.mark.parametrize(
    ("env", "asked"),
    [({}, False), ({"WINDOWS": "0"}, True)],
    ids=["native-linux", "not-a-windows-drive"],
)
def test_nothing_said_without_windows_or_its_drive(
    tmp_path: Path, env: dict[str, str], *, asked: bool
) -> None:
    """No cmd.exe (Linux, interop off), or Windows has no E:: the usual missing line."""
    with using(Locale.EN):
        missing = menu_texts().missing.replace("${folder}", _FOLDER)
        done = _run(tmp_path, f"mh audit --photos {_FOLDER}", env)
    assert not _said(tmp_path, "sudo")
    assert bool(_said(tmp_path, "cmd")) is asked
    assert missing in done.stderr
    assert "status=2" in done.stdout


def test_drive_c_is_never_asked(tmp_path: Path) -> None:
    """C: is always mounted by WSL: not a question to Windows."""
    done = _run(tmp_path, "_mh_drive /mnt/c/Photos", {"WINDOWS": "1"})
    assert "status=0" in done.stdout
    assert not _said(tmp_path, "cmd")


def test_mh_sh_runs_no_root_command(tmp_path: Path) -> None:
    """Every `sudo` of the script is in a line it prints, never a command it runs."""
    bash_mh(tmp_path, _COMMANDS, "")
    for line in (tmp_path / "mh.sh").read_text().splitlines():
        code = line.split("#", 1)[0].strip()
        if re.search(r"\bsudo\s", code):
            assert code.startswith(('"sudo ', "printf ")), line
