"""`mh` says when its own file changed since the terminal loaded it (0276)."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Final

from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_stale import stale_texts
from tests.support.host_bash import run_bash
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    import subprocess
    from pathlib import Path

_COMMANDS: Final = LauncherCommands(("audit",), (), (), (), 8088)
# `docker` prints what it was given, `version` says it is running.
_FAKE_DOCKER: Final = r"""
docker() { printf 'ran:%s\n' "$@"; }
"""


def _render(shell: Shell, tmp_path: Path) -> str:
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    return render_script(launcher_script(runtime, shell, _COMMANDS))


def _run(tmp_path: Path, between: str) -> subprocess.CompletedProcess[str]:
    """Load mh.sh, run `between`, then `mh audit`."""
    script = tmp_path / "mh.sh"
    script.write_text(_render(Shell.BASH, tmp_path), encoding="utf-8")
    code = f"{_FAKE_DOCKER}\nsource {script}\n{between}\nmh audit"
    env = {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    return run_bash(code, env)


def _line() -> str:
    """The line in English, with the command to load the file."""
    return stale_texts().changed


def test_both_scripts_carry_the_check(tmp_path: Path) -> None:
    """The PowerShell and the bash script compare the file with its load-time stamp."""
    powershell = _render(Shell.POWERSHELL, tmp_path)
    assert "function global:_mh_stale" in powershell
    assert "$global:MediaHygieneLoaded" in powershell
    assert "ScriptBlock.File" in powershell
    assert "LastWriteTimeUtc.Ticks" in powershell
    assert "-ErrorAction SilentlyContinue" in powershell
    assert powershell.isascii()
    assert "_mh_stale()" in _render(Shell.BASH, tmp_path)


def test_powershell_variables_do_not_repeat_a_parameter_name(
    tmp_path: Path,
) -> None:
    """PowerShell names ignore case: the check's own variables name no parameter."""
    powershell = _render(Shell.POWERSHELL, tmp_path)
    start = powershell.index("function global:_mh_stale")
    block = powershell[start : powershell.index("\n}\n", start)]
    assert "$reload = " in block
    assert "$path = " in block
    assert "$item = " in block


def test_bash_an_unchanged_file_says_nothing(tmp_path: Path) -> None:
    """The file as loaded: the command runs, nothing about a change."""
    result = _run(tmp_path, "")
    assert "changed on disk" not in result.stderr
    assert "ran:run" in result.stdout


def test_bash_a_file_written_again_is_said_before_the_command(tmp_path: Path) -> None:
    """One line on stderr with the `source` to type; the command still runs."""
    script = tmp_path / "mh.sh"
    result = _run(tmp_path, f"printf '# new\\n' >> '{script}'")
    assert "mh changed on disk since this window loaded it" in result.stderr
    assert f"source '{script}'" in result.stderr
    assert "ran:run" in result.stdout


def test_bash_a_touched_file_is_said_too(tmp_path: Path) -> None:
    """The write time alone differs (a copy, a `touch`): said."""
    script = tmp_path / "mh.sh"
    result = _run(tmp_path, f"touch -d '2001-01-01 00:00:00' '{script}'")
    assert "changed on disk" in result.stderr


def test_bash_a_file_removed_says_nothing(tmp_path: Path) -> None:
    """Gone or moved: the call still works from memory, quietly."""
    script = tmp_path / "mh.sh"
    result = _run(tmp_path, f"rm -f '{script}'")
    assert "changed on disk" not in result.stderr
    assert "ran:run" in result.stdout


def test_bash_loading_again_ends_the_warning(tmp_path: Path) -> None:
    """After `source`, the new file is the reference."""
    script = tmp_path / "mh.sh"
    result = _run(tmp_path, f"printf '# new\\n' >> '{script}'; source '{script}'")
    assert "changed on disk" not in result.stderr


def test_the_line_names_the_command_to_type() -> None:
    """The text holds the placeholder of the command and no quote."""
    assert "${reload}" in _line()
