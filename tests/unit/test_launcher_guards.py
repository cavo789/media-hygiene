"""`mh` before a `docker run`: a page left by a closed window, a removable drive.

TODOs 0250 (each page labelled with the PID of its console; a page whose console is gone
is stopped, a live one left alone) and 0252 (`mh.ps1` shares a removable drive with
Docker Desktop's VM before the run).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_guards import (
    DRIVE_LABEL,
    PAGE_LABEL,
    launcher_guards,
)
from tests.support.host_bash import bash_mh, run_bash
from tests.unit.test_launcher_ascii import accented_runtime, expanded

if TYPE_CHECKING:
    import subprocess

_PORT: Final = 8088
_COMMANDS: Final = LauncherCommands(
    ("audit", "review", "menu"), (), ("review",), ("menu",), _PORT
)
# A PID no process has: beyond Linux's largest `pid_max`.
_GONE: Final = 2_147_483_646
# `docker ps` prints $HELD; `docker stop` leaves a mark; `docker run` says what it got.
_FAKE_DOCKER: Final = r"""
docker() {
    case "$1" in
        ps) touch "$HOME/listed"; if [[ -n "$HELD" ]]; then printf '%s\n' "$HELD"; fi ;;
        stop) printf '%s\n' "$2" > "$HOME/stopped" ;;
        *) printf 'ran:%s\n' "$@" ;;
    esac
}
"""


def _bash(
    tmp_path: Path, line: str, held: str = ""
) -> subprocess.CompletedProcess[str]:
    """Load the bash `mh` and run `line`, `docker ps` printing `held`."""
    code = f"{bash_mh(tmp_path, _COMMANDS, _FAKE_DOCKER)}; {line}; echo status=$?"
    env = {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin", "HELD": held}
    return run_bash(code, env)


def _texts() -> tuple[str, str]:
    """The lines `stopped` and `open`, in English."""
    texts = launcher_guards().texts
    return texts.stopped, texts.open


def _started(pid: int) -> str:
    """The start time of process `pid`, as `mh.sh` writes it (field 22 of its stat)."""
    stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    return stat.rsplit(") ", 1)[1].split()[19]


def test_bash_page_is_labelled_with_its_shell(tmp_path: Path) -> None:
    """A page carries `media-hygiene.page=bash-<PID>-<start>`; a free port is quiet."""
    with using(Locale.EN):
        done = _bash(tmp_path, "mh review")
    assert "ran:--label" in done.stdout
    assert re.search(
        rf"^ran:{re.escape(PAGE_LABEL)}=bash-\d+-\d+$", done.stdout, re.MULTILINE
    )
    assert "status=0" in done.stdout
    assert not done.stderr


def test_bash_other_commands_do_not_ask_docker_ps(tmp_path: Path) -> None:
    """Only a page checks the port: an audit costs nothing more."""
    done = _bash(tmp_path, "mh audit")
    assert "ran:audit" in done.stdout
    assert "--label" not in done.stdout
    assert not (tmp_path / "listed").exists()


def test_bash_page_of_a_closed_terminal_is_stopped(tmp_path: Path) -> None:
    """Its shell is gone: stopped, one line said, the new page runs."""
    with using(Locale.EN):
        stopped, _open = _texts()
        done = _bash(tmp_path, "mh review", f"0abc12;x=1,{PAGE_LABEL}=bash-{_GONE}")
    assert (tmp_path / "stopped").read_text().strip() == "0abc12"
    assert stopped in done.stderr
    assert "ran:review" in done.stdout


def test_bash_page_of_a_live_terminal_is_left_alone(tmp_path: Path) -> None:
    """Its shell still runs (here, the test's own process): left, the user told."""
    with using(Locale.EN):
        _stopped, live = _texts()
        done = _bash(tmp_path, "mh review", f"0abc12;{PAGE_LABEL}=bash-{os.getpid()}")
    assert not (tmp_path / "stopped").exists()
    assert live in done.stderr
    assert "ran:" not in done.stdout
    assert "status=1" in done.stdout


def test_bash_page_of_a_live_terminal_started_then_is_left_alone(
    tmp_path: Path,
) -> None:
    """Its PID runs and started when the label says: the page is live."""
    pid = os.getpid()
    with using(Locale.EN):
        _stopped, live = _texts()
        held = f"0abc12;{PAGE_LABEL}=bash-{pid}-{_started(pid)}"
        done = _bash(tmp_path, "mh review", held)
    assert not (tmp_path / "stopped").exists()
    assert live in done.stderr
    assert "status=1" in done.stdout


def test_bash_page_whose_pid_was_given_again_is_stopped(tmp_path: Path) -> None:
    """The PID runs, but started at another time: another process, the page stopped."""
    pid = os.getpid()
    with using(Locale.EN):
        stopped, _open = _texts()
        held = f"0abc12;{PAGE_LABEL}=bash-{pid}-{int(_started(pid)) + 1}"
        done = _bash(tmp_path, "mh review", held)
    assert (tmp_path / "stopped").read_text().strip() == "0abc12"
    assert stopped in done.stderr
    assert "ran:review" in done.stdout


def test_bash_port_held_by_another_container_names_it(tmp_path: Path) -> None:
    """No mh label (an older mh, another program): its id and docker stop are said."""
    with using(Locale.EN):
        done = _bash(tmp_path, "mh review", "0def34;org.opencontainers.image.title=x")
    assert "docker stop 0def34" in done.stderr
    assert not (tmp_path / "stopped").exists()
    assert "status=1" in done.stdout


@pytest.mark.parametrize("locale", list(Locale))
def test_powershell_checks_the_page_and_the_removable_drives(locale: Locale) -> None:
    """mh.ps1: labelled pages, leftovers stopped, removable drives shared; ASCII."""
    with using(locale):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    shown = expanded(text)
    assert (
        f"$page += '--label', \"{PAGE_LABEL}=powershell-$PID-$(_mh_started $PID)\""
    ) in shown
    assert 'docker ps --filter "publish=8088"' in shown
    assert "Get-Process -Id $owner" in shown
    # A PID given again by Windows: live only when the start time matches too.
    assert "=powershell-(\\d+)(-(\\d*))?(,|$)'" in shown
    assert "$started -eq $since" in shown
    assert (
        ".StartTime.ToUniversalTime().ToString('yyyyMMddHHmmss', "
        "[Globalization.CultureInfo]::InvariantCulture)"
    ) in shown
    assert "docker stop $id" in shown
    assert "Get-Volume -DriveLetter $drive" in shown
    assert "'Removable'" in shown
    assert (
        'wsl.exe -d docker-desktop sh -c "mountpoint -q /mnt/host/$letter && exit 10; '
        'mkdir -p /mnt/host/$letter && mount -t drvfs ${drive}: /mnt/host/$letter"'
    ) in shown
    # The drives of every folder mounted, the --photos ones too, are checked.
    assert '$hosts = @("C:\\Photos\\Vidéos", "D:\\Été 2019"' in shown
    assert "$shared = _mh_removable $hosts" in shown
    # The check runs before the run, never with a compile or a policy bypass (Avast).
    assert shown.index("_mh_removable $hosts") < shown.index("docker run --rm")
    start = shown.index("function global:_mh_page_free")
    guards = shown[
        start : shown.index("\n}\n", shown.index("function global:_mh_unmount"))
    ]
    assert "-ExecutionPolicy" not in guards
    assert "Add-Type" not in guards


def test_powershell_lines_hold_their_variables() -> None:
    """The drive and the container id are PowerShell variables, braced."""
    with using(Locale.FR):
        texts = launcher_guards().texts
    assert "${drive}" in texts.shared
    assert "${drive}" in texts.unshared
    assert "${drive}" in texts.kept
    assert "${drive}" in texts.stuck
    assert texts.held.count("${id}") == 2


def test_powershell_unmounts_the_drives_it_mounted() -> None:
    """mh.ps1: a drive this run mounted is unmounted after the run, in finally (0252).

    Left while another mh container uses it; the exit code stays the run's.
    """
    with using(Locale.EN):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
        texts = launcher_guards().texts
    shown = expanded(text)
    # Only the drives it mounted: exit 10 = mounted already (another window, by hand).
    assert "if ($LASTEXITCODE -eq 0) { $shared.mounted += $letter }" in shown
    assert f"$shared.labels += '--label', \"{DRIVE_LABEL}.$letter=1\"" in shown
    assert "            @marks `" in shown
    run = shown.index("docker run --rm")
    unmount = shown.index("if ($shared.mounted) { _mh_unmount $shared.mounted }")
    assert run < shown.index("} finally {", run) < unmount
    body = shown[shown.index("function global:_mh_unmount") :]
    body = body[: body.index("\n}\n")]
    assert f'docker ps -q --filter "label={DRIVE_LABEL}.$letter"' in body
    assert body.index(texts.kept) < body.index("umount /mnt/host/$letter")
    assert "wsl.exe -d docker-desktop umount /mnt/host/$letter" in body
    assert texts.stuck in body
    assert "$status = $global:LASTEXITCODE" in body
    assert body.rstrip().endswith("$global:LASTEXITCODE = $status")
    # A drive that cannot be shared undoes the ones mounted before it.
    removable = shown[shown.index("function global:_mh_removable") :]
    assert "_mh_unmount $shared.mounted" in removable[: removable.index("\n}\n")]
