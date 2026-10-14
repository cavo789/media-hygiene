"""The image starts without compiling Python at run time (TODO 0139, run with `e2e`)."""

from __future__ import annotations

import re
import shutil
from typing import Final

import pytest

from tests.support.docker import IMAGE, run_image

# `python -v` names where each module comes from: a `.pyc`, or a source compiled now.
COMPILED_NOW: Final = re.compile(r"code object from '([^']+\.py)'")

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        shutil.which("docker") is None, reason="docker is not available"
    ),
]


def test_no_module_is_compiled_at_start() -> None:
    """The standard library and the venv both ship their bytecode."""
    result = run_image(
        "--entrypoint", "python", IMAGE, "-v", "-c", "import media_hygiene.cli.app"
    )
    assert result.returncode == 0, result.stderr[-2000:]
    compiled = COMPILED_NOW.findall(result.stderr)
    assert not compiled, compiled[:10]
