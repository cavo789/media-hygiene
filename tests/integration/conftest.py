"""Integration fixtures: the command line on the demo tree, and a fake Ollama."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from tests.support.cli import point_mounts
from tests.support.demo import build_demo
from tests.support.fake_ollama import FakeOllama

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.paths.locations import Locations


@pytest.fixture
def cli(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """A runner whose mount points are the test's temporary folders.

    Args:
        locations: The test mount points.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        The runner, the demo tree in its data folder.
    """
    point_mounts(locations, monkeypatch)
    build_demo(locations.data_dir)
    return CliRunner()


@pytest.fixture
def fake() -> Iterator[FakeOllama]:
    """A fake Ollama, serving for the test.

    Yields:
        The server.
    """
    with FakeOllama() as server:
        yield server
