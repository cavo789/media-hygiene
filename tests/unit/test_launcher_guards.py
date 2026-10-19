"""`mh` before a `docker run`: a page left by a closed window, a removable drive.

TODOs 0250 (each page labelled with the PID of its console; a page whose console is gone
is stopped, a live one left alone) and 0252 (`mh.ps1` shares a removable drive with
Docker Desktop's VM before the run).
"""

from __future__ import annotations

import os
from dataclasses import replace
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_guards import PAGE_LABEL, launcher_guards
from tests.support.host_bash import run_bash
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_launcher_ascii import accented_runtime, expanded

if TYPE_CHECKING:
    import subprocess
    from pathlib import Path

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
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    script = tmp_path / "mh.sh"
    script.write_text(render_script(launcher_script(runtime, Shell.BASH, _COMMANDS)))
    code = f"{_FAKE_DOCKER}\nsource {script}; {line}; echo status=$?"
    env = {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin", "HELD": held}
    return run_bash(code, env)


def _texts() -> tuple[str, str]:
    """The lines `stopped` and `open`, in English."""
    texts = launcher_guards().texts
    return texts.stopped, texts.open


def test_bash_page_is_labelled_with_its_shell(tmp_path: Path) -> None:
    """A page run carries `media-hygiene.page=bash-<PID>`; a free port says nothing."""
    with using(Locale.EN):
        done = _bash(tmp_path, "mh review")
    assert "ran:--label" in done.stdout
    assert f"ran:{PAGE_LABEL}=bash-" in done.stdout
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
    assert f"$page += '--label', \"{PAGE_LABEL}=powershell-$PID\"" in shown
    assert 'docker ps --filter "publish=8088"' in shown
    assert "Get-Process -Id $owner" in shown
    assert "docker stop $id" in shown
    assert "Get-Volume -DriveLetter $drive" in shown
    assert "'Removable'" in shown
    assert (
        'wsl.exe -d docker-desktop sh -c "mountpoint -q /mnt/host/$letter || '
        "{ mkdir -p /mnt/host/$letter && mount -t drvfs ${drive}: /mnt/host/$letter; }"
        '"'
    ) in shown
    # The drives of every folder mounted, the --photos ones too, are checked.
    assert '$hosts = @("C:\\Photos\\Vidéos", "D:\\Été 2019"' in shown
    assert "_mh_removable $hosts" in shown
    # The check runs before the run, never with a compile or a policy bypass (Avast).
    assert shown.index("_mh_removable $hosts") < shown.index("docker run --rm")
    start = shown.index("function global:_mh_page_free")
    guards = shown[
        start : shown.index("\n}\n", shown.index("function global:_mh_removable"))
    ]
    assert "-ExecutionPolicy" not in guards
    assert "Add-Type" not in guards


def test_powershell_lines_hold_their_variables() -> None:
    """The drive and the container id are PowerShell variables, braced."""
    with using(Locale.FR):
        texts = launcher_guards().texts
    assert "${drive}" in texts.shared
    assert "${drive}" in texts.unshared
    assert texts.held.count("${id}") == 2
