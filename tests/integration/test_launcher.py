"""`launcher` writes a bash function that runs each command with the right mounts."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest

from media_hygiene.constants import ExitCode
from media_hygiene.paths.mounts import MountTable
from tests.support.cli import run

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

# Stands in for docker: prints each argument it receives on its own line.
_FAKE_DOCKER = "docker() { printf '%s\\n' \"$@\"; }"


def _arguments(script: Path, home: Path, command: str) -> list[str]:
    """Load the script in bash, run `mh <command>`, return what docker received.

    Args:
        script: The launcher script.
        home: The home folder the script creates its folders in.
        command: The arguments of `mh`.

    Returns:
        The docker arguments.
    """
    bash = shutil.which("bash") or "bash"
    line = f"{_FAKE_DOCKER}; source {script}; mh {command}"
    environment = {**os.environ, "HOME": str(home)}
    # Trusted script written by the test itself, run on its temporary folder.
    done = subprocess.run(  # noqa: S603
        [bash, "-c", line], capture_output=True, text=True, check=True, env=environment
    )
    return done.stdout.splitlines()


@pytest.fixture
def mounted_data(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Make the data folder a mount point, as `-v` would.

    Args:
        locations: The test mount points.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        The data folder.
    """
    table = MountTable(frozenset({locations.data_dir}))
    monkeypatch.setattr(MountTable, "current", lambda *_args: table)
    return locations.data_dir


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not available")
def test_the_bash_launcher_picks_the_mounts_of_each_command(
    cli: CliRunner, tmp_path: Path, mounted_data: Path
) -> None:
    """Script on stdout, messages on stderr; :ro, -p and the folders per command."""
    result = run(cli, "launcher", "--shell", "bash")
    assert result.exit_code == 0, result.output
    assert "Launcher written" not in result.stdout
    assert "source" in result.stderr
    assert "mh.sh" in result.stderr
    assert "mh remembers: 1 folder, language en" in result.stderr
    script = tmp_path / "mh.sh"
    script.write_text(result.stdout, encoding="utf-8")
    home = tmp_path / "home"
    audit = _arguments(script, home, "--locale fr audit")
    assert audit[:3] == ["run", "--rm", "-i"]
    assert "MEDIA_HYGIENE_LAUNCHER=1" in audit
    assert audit[-3:] == ["--locale", "fr", "audit"]
    assert f"/:{mounted_data}:ro" in audit
    assert "-p" not in audit
    clean = _arguments(script, home, "clean --yes")
    assert f"/:{mounted_data}" in clean
    review = _arguments(script, home, "review")
    assert review[review.index("-p") + 1] == "127.0.0.1:8088:8088"


def test_without_a_photo_folder_the_launcher_says_how_to_add_one(
    cli: CliRunner,
) -> None:
    """No data mount: no folder in the script, a warning on stderr."""
    result = run(cli, "launcher", "--shell", "powershell")
    assert result.exit_code == 0, result.output
    assert "No photo folder mounted" in result.stderr
    assert "${mode}" not in result.stdout


def test_on_a_terminal_the_launcher_writes_nothing_and_says_how(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`docker run -it … launcher`: only a refusal, which stops its own loading."""
    monkeypatch.setattr("media_hygiene.console.output.data_on_terminal", lambda: True)
    result = run(cli, "launcher", "--shell", "powershell")
    assert result.exit_code == ExitCode.USAGE, result.output
    assert "function mh" not in result.stdout
    assert "Launcher written" not in result.output
    assert result.stdout.startswith("# Nothing written")
    assert "mh.ps1" in result.stdout
    assert result.stdout.splitlines()[-1].startswith("throw ")
    assert not result.stderr
