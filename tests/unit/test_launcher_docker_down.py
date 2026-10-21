"""`mh` when Docker is not started: one line saying so, its exit code kept (0174)."""

from __future__ import annotations

import re
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
from media_hygiene.services.launcher_menu import UNSAFE_CHARACTERS, menu_texts
from tests.support.host_bash import bash_mh, run_bash
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_launcher_ascii import accented_runtime, expanded

if TYPE_CHECKING:
    import subprocess
    from pathlib import Path

_COMMANDS: Final = LauncherCommands(
    ("audit", "history", "menu"), (), (), ("menu",), 8088
)
# `docker run` exits with $RUN; `docker version` with $VERSION, and leaves a mark.
_FAKE_DOCKER: Final = r"""
docker() {
    if [[ "$1" == version ]]; then
        touch "$HOME/asked"
        return "$VERSION"
    fi
    echo "docker: $*" >&2
    return "$RUN"
}
"""
_DAEMON: Final = (
    "Docker is not started: start it (Docker Desktop, or the docker service), "
    "then type the command again."
)


def _bash(
    tmp_path: Path, line: str, answers: tuple[int, int]
) -> subprocess.CompletedProcess[str]:
    """Load the bash `mh` and run `line`; docker exits with `answers` (run, version)."""
    run, version = answers
    code = f"{bash_mh(tmp_path, _COMMANDS, _FAKE_DOCKER)}; {line}; echo status=$?"
    env = {
        "HOME": str(tmp_path),
        "PATH": "/usr/bin:/bin",
        "RUN": str(run),
        "VERSION": str(version),
    }
    return run_bash(code, env)


@pytest.mark.parametrize("version", [1, 0])
def test_bash_failed_run_asks_docker_and_keeps_the_exit_code(
    tmp_path: Path, version: int
) -> None:
    """The run failed: the line only when the daemon does not answer either."""
    done = _bash(tmp_path, "mh history", (125, version))
    assert "status=125" in done.stdout
    assert (_DAEMON in done.stderr) is (version != 0)


def test_bash_successful_run_does_not_ask_docker(tmp_path: Path) -> None:
    """A run that worked costs nothing more: `docker version` is not called."""
    done = _bash(tmp_path, "mh history", (0, 1))
    assert "status=0" in done.stdout
    assert _DAEMON not in done.stderr
    assert not (tmp_path / "asked").exists()


def test_bash_menu_says_it_once_and_asks_nothing(tmp_path: Path) -> None:
    """`mh menu`: the captured `menu` run says it; the menu stops there."""
    done = _bash(tmp_path, "mh menu < /dev/null", (1, 1))
    assert done.stderr.count(_DAEMON) == 1
    assert "Step number" not in done.stderr
    assert "status=0" not in done.stdout


def test_powershell_checks_docker_desktop_after_a_failed_run() -> None:
    """mh.ps1: `docker version` after a failure, a start, the run's exit code back."""
    with using(Locale.FR):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    back = expanded(text)
    check = back.index("    if ($status -ne 0) {\n")
    asked = back.index("        $null = docker version 2>$null\n", check)
    started = back.index("(_mh_desktop_start)", asked)
    assert started < back.index("        $global:LASTEXITCODE = $status\n", started)
    assert back.index("        $status = $LASTEXITCODE\n") < check


def test_no_translation_breaks_the_docker_lines() -> None:
    """Neither quote, dollar, backtick nor backslash, in both languages."""
    for locale in Locale:
        with using(locale):
            texts = menu_texts()
        for text in (texts.desktop, texts.daemon, texts.starting, texts.ready):
            assert text
            assert not set(text) & UNSAFE_CHARACTERS


def _powershell() -> str:
    """The French mh.ps1, its escapes expanded as PowerShell reads them."""
    with using(Locale.FR):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    return expanded(text)


def test_powershell_starts_docker_desktop_and_waits_for_it() -> None:
    """`docker desktop start --timeout 180`, asked again; 0174's line on failure."""
    back = _powershell()
    start = back.index("function global:_mh_desktop_start {\n")
    said = back.index(
        "Write-Host \"Docker Desktop n'est pas démarré : je le lance", start
    )
    started = back.index(
        "    $null = docker desktop start --timeout 180 2>$null\n", said
    )
    again = back.index(
        "    if ($LASTEXITCODE -eq 0) { $null = docker version 2>$null }\n", started
    )
    failed = back.index("Docker Desktop n'est pas démarré : lancez-le", again)
    assert failed < back.index("    return $false\n", failed)


def test_powershell_menu_paths_check_docker_desktop_first() -> None:
    """`mh` alone and `mh menu`: the check, then the page or the menu on success."""
    back = _powershell()
    checked = "        if (-not (_mh_desktop)) { return }\n"
    alone = back.index("    if ($rest.Count -eq 0) {\n")
    assert back.index(checked, alone) < back.index("        _mh_home @typed\n", alone)
    menu = back.index("    if ($rest.Count -eq 1 -and $rest[0] -eq 'menu') {\n")
    assert back.index(checked, menu) < back.index("        _mh_menu @typed\n", menu)
    lan = back.index("    if ($rest.Count -eq 1 -and $rest[0] -eq '--lan') {\n")
    assert back.index(checked, lan) < back.index("        _mh_lan @typed\n", lan)
    assert back.count(checked) == 3  # mh alone, mh --lan (0269), mh menu
    desktop = back.index("function global:_mh_desktop {\n")
    asked = back.index("    $null = docker version 2>$null\n", desktop)
    assert asked < back.index("    return (_mh_desktop_start)\n", asked)


def test_powershell_failed_command_is_never_run_twice() -> None:
    """After a failed run: Docker Desktop started, the user types the command again."""
    back = _powershell()
    check = back.index("    if ($status -ne 0) {\n")
    end = back.index("        $global:LASTEXITCODE = $status\n", check)
    block = back[check:end]
    assert "if ($LASTEXITCODE -ne 0 -and (_mh_desktop_start)) {" in block
    assert "tapez de nouveau la commande" in block
    assert "docker run" not in block
    assert back.count("        docker run --rm @tty `\n") == 1


def test_each_powershell_function_is_defined_once() -> None:
    """A second definition silently replaces the first (2026-10-19).

    `_mh_start` of the Explorer entry replaced the one starting Docker Desktop:
    `mh` printed a command line instead of starting it, then said it was ready.
    """
    names = re.findall(r"^function global:(\S+?)[ ({]", _powershell(), re.MULTILINE)
    assert {"_mh_desktop_start", "_mh_start"} <= set(names)
    assert len(names) == len(set(names)), sorted(n for n in names if names.count(n) > 1)


def test_each_bash_function_is_defined_once(tmp_path: Path) -> None:
    """The same in mh.sh: a function defined twice keeps only the last one."""
    runtime = make_runtime(make_locations(tmp_path))
    text = render_script(launcher_script(runtime, Shell.BASH, _COMMANDS))
    names = re.findall(r"^(\w+)\(\) \{", text, re.MULTILINE)
    assert names
    assert len(names) == len(set(names)), sorted(n for n in names if names.count(n) > 1)
