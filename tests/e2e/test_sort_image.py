"""The real image: classify on :ro, sort read-write, undo gives the tree back."""

from __future__ import annotations

import shutil

import pytest

from tests.e2e.test_docker_image import manifest
from tests.support.docker import tool

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        shutil.which("docker") is None, reason="docker is not available"
    ),
]


def test_classify_sort_undo_cycle(volumes: dict[str, str]) -> None:
    """Sorting moves files and proves it; undo restores every byte and date."""
    before = manifest(volumes)
    classify = tool(volumes, "classify", read_only_data=True)
    assert classify.startswith("0\n"), classify
    refused = tool(volumes, "sort", "--yes", read_only_data=True)
    assert refused.startswith("1\n"), refused
    assert "read-only" in refused
    sort = tool(volumes, "sort", "--yes")
    assert sort.startswith("0\n"), sort
    assert "Nothing lost" in sort
    assert manifest(volumes) != before
    undo = tool(volumes, "undo")
    assert undo.startswith("0\n"), undo
    assert manifest(volumes) == before
