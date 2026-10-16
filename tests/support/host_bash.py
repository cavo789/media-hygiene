"""The host side of `mh`: a bash run with fake programs first on `PATH`."""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


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
