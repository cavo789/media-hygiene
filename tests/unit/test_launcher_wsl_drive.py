"""`mh.sh` in WSL: a drive WSL has not mounted (a USB stick) is mounted for the command.

TODO 0254: WSL mounts the drives present when it starts; a stick plugged in later is
absent from `/mnt`. `mh.sh` mounts it with sudo (`mount -t drvfs`) before the command,
then unmounts it, unless another `mh` container uses it. Native Linux: nothing changes.
Each case runs the real bash functions with fake `mountpoint`, `cmd.exe`, `sudo` and
`docker`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import Shell
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_guards import DRIVE_LABEL, launcher_guards
from media_hygiene.services.launcher_menu import menu_texts
from tests.support.host_bash import bash_mh, run_bash
from tests.unit.test_launcher_ascii import accented_runtime

if TYPE_CHECKING:
    import subprocess
    from pathlib import Path

    from media_hygiene.services.launcher_guards import WslTexts

_COMMANDS: Final = LauncherCommands(("audit", "review"), (), ("review",), (), 8088)
_FOLDER: Final = "/mnt/e/Photos"
# $MOUNTED: `mountpoint` says the drive is mounted; $WINDOWS: `cmd.exe /c vol` finds it
# (unset: no cmd.exe, native Linux); $SUDO: sudo's exit code; $USERS: `docker ps -q`.
_FAKES: Final = r"""
mountpoint() { [[ -n "${MOUNTED:-}" ]]; }
if [[ -n "${WINDOWS+set}" ]]; then
    cmd.exe() { printf '%s\n' "$*" >> "$HOME/cmd"; [[ "$WINDOWS" == 1 ]]; }
fi
sudo() { printf '%s\n' "$*" >> "$HOME/sudo"; return "${SUDO:-0}"; }
docker() {
    case "$1" in
        ps) printf '%s' "${USERS:-}" ;;
        *) printf 'ran:%s\n' "$@" ;;
    esac
}
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


def test_drive_absent_from_wsl_is_mounted_then_unmounted(tmp_path: Path) -> None:
    """Windows has E:, WSL has not: mounted with sudo, said, unmounted after."""
    with using(Locale.EN):
        texts = _texts()
        missing = menu_texts().missing.replace("${folder}", _FOLDER)
        done = _run(tmp_path, f"mh audit --photos {_FOLDER}", {"WINDOWS": "1"})
    assert _said(tmp_path, "cmd") == ["/c vol E:"]
    sudo = _said(tmp_path, "sudo")
    assert sudo[0] == "mkdir -p /mnt/e"
    # Owned by the user, as WSL mounts its own drives: the container runs as the user.
    assert sudo[1].startswith("mount -t drvfs E: /mnt/e -o uid=")
    assert ",gid=" in sudo[1]
    assert _filled(texts.mount) in done.stderr
    # The folder of the fake drive is not there: the usual line, then unmounted.
    assert missing in done.stderr
    assert _said(tmp_path, "sudo")[-1] == "umount /mnt/e"
    assert "status=2" in done.stdout


def test_drive_mounted_and_labelled_for_the_container(tmp_path: Path) -> None:
    """The drive mounted goes to `mounted`, its label to `marks`, once each."""
    line = (
        "mounted=(); marks=(); _mh_drive /mnt/e/Photos; _mh_drive /mnt/e/Videos; "
        'echo "mounted=${mounted[*]} marks=${marks[*]}"'
    )
    done = _run(tmp_path, line, {"WINDOWS": "1"})
    assert f"mounted=e marks=--label {DRIVE_LABEL}.e=1\n" in done.stdout
    assert _said(tmp_path, "sudo").count("mkdir -p /mnt/e") == 1


def test_drive_already_mounted_is_left_alone(tmp_path: Path) -> None:
    """WSL has it (at its start, by hand, by another mh): no sudo, never unmounted."""
    line = (
        "mounted=(); marks=(); _mh_drive /mnt/e/Photos; "
        'echo "mounted=${mounted[*]} marks=${marks[*]}"'
    )
    done = _run(tmp_path, line, {"WINDOWS": "1", "MOUNTED": "1"})
    assert f"mounted= marks=--label {DRIVE_LABEL}.e=1\n" in done.stdout
    assert not _said(tmp_path, "sudo")
    assert not _said(tmp_path, "cmd")


@pytest.mark.parametrize(
    ("env", "asked"),
    [({}, False), ({"WINDOWS": "0"}, True)],
    ids=["native-linux", "not-a-windows-drive"],
)
def test_nothing_mounted_without_windows_or_its_drive(
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


def test_mount_failure_stops_with_the_advice(tmp_path: Path) -> None:
    """Sudo refused (no password, no right): one line, nothing runs."""
    with using(Locale.EN):
        texts = _texts()
        done = _run(
            tmp_path, f"mh audit --photos {_FOLDER}", {"WINDOWS": "1", "SUDO": "1"}
        )
    assert _filled(texts.failed) in done.stderr
    assert "sudo mount -t drvfs E: /mnt/e" in _filled(texts.failed)
    assert "ran:" not in done.stdout
    assert "status=1" in done.stdout
    assert "umount /mnt/e" not in _said(tmp_path, "sudo")


def test_drive_another_mh_uses_stays_mounted(tmp_path: Path) -> None:
    """Another mh container carries the drive's label: left mounted, said."""
    line = "mounted=(e); _mh_release"
    with using(Locale.EN):
        texts = _texts()
        done = _run(tmp_path, line, {"USERS": "0abc12\n"})
    assert _filled(texts.kept) in done.stderr
    assert not _said(tmp_path, "sudo")


def test_unmount_failure_is_said(tmp_path: Path) -> None:
    """Umount refused (the stick busy): one line, the way to do it by hand."""
    with using(Locale.EN):
        texts = _texts()
        done = _run(tmp_path, "mounted=(e); _mh_release", {"SUDO": "1"})
    assert _said(tmp_path, "sudo") == ["umount /mnt/e"]
    assert _filled(texts.stuck) in done.stderr


def test_drive_c_is_never_asked(tmp_path: Path) -> None:
    """C: is always mounted by WSL: not a label, not a question to Windows."""
    line = 'mounted=(); marks=(); _mh_drive /mnt/c/Photos; echo "marks=${marks[*]}"'
    done = _run(tmp_path, line, {"WINDOWS": "1"})
    assert "marks=\n" in done.stdout
    assert not _said(tmp_path, "cmd")


def test_the_run_carries_the_drive_labels_and_releases_after() -> None:
    """mh.sh: the labels on docker run; the drives released after every command."""
    with using(Locale.EN):
        text = render_script(launcher_script(accented_runtime(), Shell.BASH, _COMMANDS))
    assert '"${page[@]}" "${marks[@]}" \\' in text
    wrapper = text[text.index("\nmh() {") :]
    wrapper = wrapper[: wrapper.index("\n}\n")]
    assert "local mounted=() marks=() status=0" in wrapper
    assert wrapper.index("_mh_command") < wrapper.index("_mh_release")
    checked = text.index('_mh_drive "$folder" || return 1\n        if [[ ! -d')
    assert checked < text.index("docker run --rm")
