"""Fixtures: a fake Ollama, and the command line on three synthetic events."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from media_hygiene.paths.mount_kind import MountKind
from tests.support.fake_ollama import FakeOllama
from tests.support.subjects import write_config, write_events

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.paths.locations import Locations


@pytest.fixture
def fake() -> Iterator[FakeOllama]:
    """A fake Ollama, serving for the test.

    Yields:
        The server.
    """
    with FakeOllama() as server:
        yield server


@pytest.fixture
def cli(
    locations: Locations, monkeypatch: pytest.MonkeyPatch, fake: FakeOllama
) -> CliRunner:
    """A runner on three synthetic events, its only rule asking the fake model.

    Args:
        locations: The test mount points.
        monkeypatch: Pytest monkeypatch fixture.
        fake: The fake model server.

    Returns:
        The runner.
    """
    for kind in MountKind:
        monkeypatch.setenv(
            f"MEDIA_HYGIENE_{kind.value.upper()}_DIR", str(locations.path_of(kind))
        )
    write_events(locations.data_dir)
    write_config(locations.config_dir, fake.url)
    return CliRunner()
