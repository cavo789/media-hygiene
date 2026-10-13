"""Commands that never open a picture never load libheif nor LibRaw."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING, Final

from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    from pathlib import Path

# Run in a fresh interpreter: the test process itself has loaded every decoder.
_PROBE: Final = """
import sys
from typer.testing import CliRunner
from media_hygiene.cli.app import build_app
for command in (["--help"], ["undo"], ["history"], ["purge"], ["config"]):
    CliRunner().invoke(build_app(), command)
print(sorted(m for m in ("pillow_heif", "rawpy") if m in sys.modules))
"""


def test_undo_history_purge_config_load_no_decoder(tmp_path: Path) -> None:
    """Neither `pillow_heif` nor `rawpy` is imported by these commands."""
    env = {**os.environ}
    for kind in MountKind:
        folder = tmp_path / kind.value
        folder.mkdir()
        env[f"MEDIA_HYGIENE_{kind.value.upper()}_DIR"] = str(folder)
    # The test's own interpreter, on a script written above.
    done = subprocess.run(  # noqa: S603
        [sys.executable, "-c", _PROBE],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().splitlines()[-1] == "[]"
