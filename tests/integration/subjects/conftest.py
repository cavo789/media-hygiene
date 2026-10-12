"""Fixtures: the command line on three synthetic events, its model a fake Ollama."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from tests.support.cli import point_mounts
from tests.support.subjects import write_config, write_events

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from tests.support.fake_ollama import FakeOllama


@pytest.fixture
def cli(
    locations: Locations, monkeypatch: pytest.MonkeyPatch, fake: FakeOllama
) -> CliRunner:
    """A runner on three synthetic events, its only rule asking the fake model.

    Args:
        locations: The test mount points.
        monkeypatch: Pytest monkeypatch fixture.
        fake: The fake model server (`fake`, tests/integration/conftest.py).

    Returns:
        The runner.
    """
    point_mounts(locations, monkeypatch)
    write_events(locations.data_dir)
    write_config(locations.config_dir, fake.url)
    return CliRunner()
