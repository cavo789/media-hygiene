"""The real image: `docker stop` ends an audit like Ctrl+C, the index kept (0143)."""

from __future__ import annotations

import shutil
import time
from typing import Final

import pytest

from media_hygiene.constants import ExitCode
from tests.support.docker import IMAGE, docker

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        shutil.which("docker") is None, reason="docker is not available"
    ),
]

# Enough large pictures, decoded on half a processor, to keep the checks busy for a
# while: the stop lands in the middle of them. PNG: no reduced decode as for JPEG.
_PICTURES: Final = 150
_SEED: Final = f"""
import shutil
from pathlib import Path
from PIL import Image
folder = Path("/data/c/Big")
folder.mkdir(parents=True, exist_ok=True)
first = folder / "0000.png"
Image.linear_gradient("L").resize((3000, 2000)).convert("RGB").save(first)
for number in range(1, {_PICTURES}):
    shutil.copy(first, folder / f"{{number:04}}.png")
"""
_COUNT: Final = (
    "import sqlite3; print(sqlite3.connect('/cache/index.sqlite')"
    ".execute('SELECT COUNT(*) FROM files WHERE integrity_checked').fetchone()[0])"
)
_STARTED_SECONDS: Final = 5.0
_STOP_GRACE: Final = "10"  # Docker's default: SIGTERM, then SIGKILL 10 s later
_STOPPED_WITHIN: Final = 9.0


def mounts(volumes: dict[str, str]) -> list[str]:
    """Every mount point, on its named volume."""
    return [option for kind, name in volumes.items()
            for option in ("-v", f"{name}:/{kind}")]  # fmt: skip


def run_python(volumes: dict[str, str], script: str) -> str:
    """Run a Python snippet in the image, with the volumes, and return its output."""
    started = docker("run", "--detach", *mounts(volumes), "--entrypoint", "python",
                     IMAGE, "-c", script)  # fmt: skip
    container = started.stdout.strip()
    docker("wait", container)
    output = docker("logs", container)
    docker("rm", container)
    return output.stdout + output.stderr


def test_docker_stop_ends_an_audit_like_ctrl_c(volumes: dict[str, str]) -> None:
    """Stopped in the middle of its checks, the audit exits 130 and keeps them."""
    run_python(volumes, _SEED)
    started = docker("run", "--detach", "--cpus", "0.5", *mounts(volumes),
                     IMAGE, "audit")  # fmt: skip
    container = started.stdout.strip()
    try:
        time.sleep(_STARTED_SECONDS)
        stopping = time.monotonic()
        docker("stop", "--time", _STOP_GRACE, container)
        took = time.monotonic() - stopping
        state = docker("inspect", "--format", "{{.State.ExitCode}}", container)
        logs = docker("logs", container)
    finally:
        docker("rm", "--force", container)
    output = logs.stdout + logs.stderr
    assert int(state.stdout) == ExitCode.INTERRUPTED, output
    assert took < _STOPPED_WITHIN, output
    assert "Traceback" not in output
    kept = int(run_python(volumes, _COUNT).strip())
    assert 0 < kept < _PICTURES
