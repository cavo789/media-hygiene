"""The real image: `crosscheck` runs the Czkawka it ships, then compares, in one go."""

from __future__ import annotations

import shutil

import pytest

from tests.support.docker import tool

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        shutil.which("docker") is None, reason="docker is not available"
    ),
]


def test_crosscheck_alone_gives_a_second_opinion(volumes: dict[str, str]) -> None:
    """No other image, no command to paste: Czkawka runs and agrees, twice."""
    first = tool(volumes, "crosscheck", read_only_data=True)
    assert first.startswith("0\n"), first
    assert "Czkawka finished in" in first
    assert "Czkawka agrees" in first
    # Its cache on /cache, its results replaced: a second run agrees again.
    again = tool(volumes, "crosscheck", "--fresh", read_only_data=True)
    assert again.startswith("0\n"), again
    assert "Czkawka agrees" in again
    assert "Traceback" not in first + again
