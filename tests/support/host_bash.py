"""The host side of `mh`: a bash run with fake programs first on `PATH`."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import launcher_script, render_script
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.launcher import LauncherCommands


def run_bash(code: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run `code` in bash with `env` only, one minute at most.

    Args:
        code: The bash code (the fake `docker`, the sourced `mh`, the line to run).
        env: The whole environment of the run.

    Returns:
        The finished run, its output captured as text.
    """
    bash = shutil.which("bash") or "bash"
    # Trusted script written by the test itself, run on its temporary folder.
    return subprocess.run(  # noqa: S603
        [bash, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=60,
    )


def fake_program(folder: Path, name: str, body: str) -> None:
    """Write an executable bash program `name` into `folder` (created if needed).

    Args:
        folder: The folder of the fake host programs.
        name: The program's name.
        body: Its bash code.
    """
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(f"#!/bin/bash\n{body}\n", encoding="utf-8")
    path.chmod(0o755)


def bash_mh(tmp_path: Path, commands: LauncherCommands, fake_docker: str) -> str:
    """Write the bash `mh` (no mount) into `tmp_path`; the code defining and loading it.

    Args:
        tmp_path: The test's temporary folder.
        commands: The verbs the launcher knows.
        fake_docker: The bash code of the fake `docker` function.

    Returns:
        `fake_docker`, then the line sourcing `mh.sh`: append `; <line>` to run one.
    """
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    script = tmp_path / "mh.sh"
    script.write_text(render_script(launcher_script(runtime, Shell.BASH, commands)))
    return f"{fake_docker}\nsource {script}"
