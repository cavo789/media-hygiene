"""Starting the tool for `--version` or `--help` loads no heavy library (TODO 0136)."""

from __future__ import annotations

import subprocess
import sys
from typing import Final

import pytest

_HEAVY: Final = ("numpy", "openpyxl", "PIL", "jinja2", "rawpy", "cv2")
_PROBE: Final = """
import runpy, sys
sys.argv = ["media-hygiene", *sys.argv[1:]]
try:
    runpy.run_module("media_hygiene", run_name="__main__")
except SystemExit:
    pass
print("loaded:" + ",".join(sorted(name for name in {heavy} if name in sys.modules)))
"""


@pytest.mark.parametrize("args", [("--version",), ("--help",), ("status", "--help")])
def test_no_heavy_library_at_start(args: tuple[str, ...]) -> None:
    """Each command imports its own code only when it runs."""
    probe = _PROBE.format(heavy=_HEAVY)
    found = subprocess.run(  # noqa: S603 - the test's own interpreter and probe
        [sys.executable, "-c", probe, *args],
        capture_output=True,
        text=True,
        check=True,
    )
    loaded = found.stdout.strip().splitlines()[-1].removeprefix("loaded:")
    assert not loaded, f"loaded at start: {loaded}"
