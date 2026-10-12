"""Fixtures: the command line on plain coloured pictures, a fake face finder."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from media_hygiene.services import people as people_service
from media_hygiene.services import people_page
from tests.support.cli import point_mounts, run
from tests.support.faces import FakeRecipe, coloured

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.paths.locations import Locations

# Person 0 on four photos, person 1 on three, person 2 on one, nobody on two.
PEOPLE = (0, 0, 0, 0, 1, 1, 1, 2, -1, -1)
PORT = 8766


def served(groups: list[object]) -> Callable[..., object]:
    """A server that keeps the app it was given, says it is ready, then gets Ctrl+C.

    Args:
        groups: Receives the app.

    Returns:
        The fake `run_server`.
    """

    async def serve(app: object, _port: int, ready: Callable[[int], None]) -> None:
        groups.append(app)
        ready(PORT)
        raise KeyboardInterrupt

    return serve


@pytest.fixture
def apps(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """The page apps served, the faces found by the fake finder.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        The apps the command served, in order.
    """
    found: list[object] = []
    monkeypatch.setattr(people_page, "run_server", served(found))
    monkeypatch.setattr(people_service, "face_recipe", lambda _runtime: FakeRecipe())
    return found


@pytest.fixture
def cli(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """A runner on the coloured pictures, audited.

    Args:
        locations: The test mount points.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        The runner.
    """
    point_mounts(locations, monkeypatch)
    for number, person in enumerate(PEOPLE):
        folder = "Family" if number % 2 else "Holidays"
        coloured(locations.data_dir / "c" / folder / f"IMG_{number}.png", person)
    runner = CliRunner()
    audited = run(runner, "audit")
    assert audited.exit_code == 0, audited.output
    return runner
