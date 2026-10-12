"""Fixtures: the command line on events, a burst and a copy, its model a fake Ollama."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from tests.support.cli import point_mounts, run
from tests.support.tagging import write_tags_config, write_tree

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from tests.support.fake_ollama import FakeOllama


@pytest.fixture
def cli(
    locations: Locations, monkeypatch: pytest.MonkeyPatch, fake: FakeOllama
) -> CliRunner:
    """A runner on the tree, audited, its model the fake one.

    Args:
        locations: The test mount points.
        monkeypatch: Pytest monkeypatch fixture.
        fake: The fake model server (`fake`, tests/integration/conftest.py).

    Returns:
        The runner.
    """
    point_mounts(locations, monkeypatch)
    write_tree(locations.data_dir)
    write_tags_config(locations.config_dir, fake.url)
    runner = CliRunner()
    audited = run(runner, "audit")
    assert audited.exit_code == 0, audited.output
    assert fake.calls == []  # an audit never asks the model
    return runner
