"""`mh` when Docker is not started: one line saying so, its exit code kept (0174)."""

from __future__ import annotations

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
from media_hygiene.services.launcher_menu import UNSAFE_CHARACTERS, menu_texts
from tests.support.host_bash import run_bash
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
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    script = tmp_path / "mh.sh"
    script.write_text(render_script(launcher_script(runtime, Shell.BASH, _COMMANDS)))
    code = f"{_FAKE_DOCKER}\nsource {script}; {line}; echo status=$?"
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
    """`mh` alone: the captured `menu` run says it; the menu stops there."""
    done = _bash(tmp_path, "mh < /dev/null", (1, 1))
    assert done.stderr.count(_DAEMON) == 1
    assert "Step number" not in done.stderr
    assert "status=0" not in done.stdout


def test_powershell_checks_docker_desktop_after_a_failed_run() -> None:
    """mh.ps1: `docker version` after a failure, the line, the run's exit code back."""
    with using(Locale.FR):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    back = expanded(text)
    check = back.index("    if ($status -ne 0) {\n")
    asked = back.index("        $null = docker version 2>$null\n", check)
    said = back.index(
        "Write-Host \"Docker Desktop n'est pas démarré : lancez-le", asked
    )
    assert said < back.index("        $global:LASTEXITCODE = $status\n", said)
    assert back.index("        $status = $LASTEXITCODE\n") < check


def test_no_translation_breaks_the_docker_lines() -> None:
    """Neither quote, dollar, backtick nor backslash, in both languages."""
    for locale in Locale:
        with using(locale):
            texts = menu_texts()
        for text in (texts.desktop, texts.daemon):
            assert text
            assert not set(text) & UNSAFE_CHARACTERS
