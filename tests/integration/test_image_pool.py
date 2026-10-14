"""The image pool's fork server imports what workers need, never the CLI (0140)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Final

_ROOT: Final = Path(__file__).resolve().parents[2]
# A `__main__` that loads the command line, as the `media-hygiene` script does.
_SCRIPT: Final = """
import media_hygiene.__main__
from media_hygiene.services.runtime import process_pool, warm_pool
from tests.support.pool_probe import cli_loaded

if __name__ == "__main__":
    warm_pool()
    with process_pool() as pool:
        print("cli in worker:", pool.submit(cli_loaded).result())
"""


def test_workers_never_load_the_command_line(tmp_path: Path) -> None:
    """The fork server does not import `__main__`, which holds the whole CLI."""
    script = tmp_path / "entry.py"
    script.write_text(_SCRIPT, encoding="utf-8")
    found = subprocess.run(  # noqa: S603 - the test's own interpreter and script
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        check=True,
        cwd=_ROOT,
        env={"PYTHONPATH": str(_ROOT)},
    )
    assert "cli in worker: False" in found.stdout, found.stderr[-2000:]
