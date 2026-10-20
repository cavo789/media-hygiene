"""Shared fixtures: an isolated set of mount points and a media factory inside it."""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from tests.support.media import MediaFactory
from tests.support.runtime import make_locations

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.paths.locations import Locations


@pytest.fixture(autouse=True)
def plain_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Render every output as for a pipe, whatever the environment of the tests.

    Typer forces terminal output (colours, 80-column panels) for its help when
    `GITHUB_ACTIONS`, `FORCE_COLOR` or `PY_COLORS` is set, and Rich colours everything
    under `FORCE_COLOR`: asserted texts would then depend on where the tests run.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    monkeypatch.setattr("typer.rich_utils.FORCE_TERMINAL", False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never ask Docker Hub for a newer version: no network in the tests (0267).

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """

    def refuse(url: str) -> bytes:
        raise OSError(url)

    monkeypatch.setattr("media_hygiene.services.update_check.fetch_tags", refuse)


@pytest.fixture(autouse=True)
def english() -> Iterator[None]:
    """Run every test in English, whatever a previous test installed."""
    install(Locale.EN)
    yield
    install(Locale.EN)


@pytest.fixture
def process_zone() -> Iterator[None]:
    """Give the process zone back after the test, whatever it set."""
    saved = os.environ.get("TZ")
    yield
    if saved is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = saved
    time.tzset()


@pytest.fixture
def locations(tmp_path: Path) -> Locations:
    """Every mount point, explicit and persistent, below `tmp_path`.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        The locations.
    """
    return make_locations(tmp_path)


@pytest.fixture
def media(locations: Locations) -> MediaFactory:
    """A media factory writing into the data mount point.

    Args:
        locations: The test mount points.

    Returns:
        The factory.
    """
    return MediaFactory(locations.data_dir)
