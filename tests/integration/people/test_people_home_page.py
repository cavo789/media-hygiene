"""The face scan of `people` run by the home page (0424): figures, Stop, resume."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from media_hygiene.cli.home_people import page_people
from media_hygiene.review.home_tags_api import MEANING_PATH, PEOPLE_PATH, TAGS_PATH
from media_hygiene.services import people as people_service
from media_hygiene.services.home import home_page
from media_hygiene.services.home_tags import HomeTags
from media_hygiene.services.home_tags_models import TagsPhase, TagsRunner
from media_hygiene.services.people import PeopleStep
from tests.integration.people.conftest import PEOPLE
from tests.support.faces import FakeRecipe
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.console.page_progress import PageProgress
    from media_hygiene.paths.locations import Locations

_POLL = 0.01


def _wait(run: HomeTags) -> None:
    """Wait for the half running to end, as the page polls."""
    while run.state().phase in {TagsPhase.PREPARING, TagsPhase.RUNNING}:
        time.sleep(_POLL)


def _missing(locations: Locations) -> int:
    with PeopleStep(make_runtime(locations)) as step:
        return len(step.plan(()).missing)


def test_the_page_counts_then_scans_stops_and_resumes(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Figures first; a stop keeps the faces found; the next run finishes."""
    del cli  # the coloured tree, audited
    monkeypatch.setattr(people_service, "face_recipe", lambda _runtime: FakeRecipe())
    runtime = make_runtime(locations)
    real = page_people(runtime)
    seen: list[int] = []

    def two(progress: PageProgress, stopped: Callable[[], bool]) -> tuple[str, ...]:
        """The real scan, stopped after two photos as by Stop."""
        seen.clear()
        return real.describe(progress, lambda: stopped() or _counted(seen) > 2)

    run = HomeTags(TagsRunner(real.prepare, two))
    assert run.prepare()
    _wait(run)
    state = run.state()
    assert state.phase is TagsPhase.ASKING, state.error
    assert state.figures is not None
    assert state.figures.to_describe == len(PEOPLE)
    assert state.figures.seconds_per_photo > 0
    assert run.describe(None)
    _wait(run)
    state = run.state()
    assert state.phase is TagsPhase.DONE, state.error
    assert "kept in the cache" in state.lines[0]
    left = _missing(locations)
    assert 0 < left < len(PEOPLE)
    whole = HomeTags(real)
    assert whole.prepare()
    _wait(whole)
    assert whole.describe(None)
    _wait(whole)
    assert whole.state().phase is TagsPhase.DONE, whole.state().error
    assert _missing(locations) == 0
    assert "groups of faces" in " ".join(whole.state().lines)


def test_no_photo_is_one_line(locations: Locations) -> None:
    """An empty index: the page says to audit first, never a traceback."""
    run = HomeTags(page_people(make_runtime(locations)))
    assert run.prepare()
    _wait(run)
    state = run.state()
    assert state.phase is TagsPhase.FAILED
    assert state.error
    assert "audit" in state.error


def _counted(seen: list[int]) -> int:
    """Count one more question "stop now?"."""
    seen.append(0)
    return len(seen)


def test_the_page_offers_only_the_runs_it_serves() -> None:
    """The faces and meaning paths are in the page only when served there."""
    plain = home_page().decode()
    assert PEOPLE_PATH not in plain
    assert MEANING_PATH not in plain
    both = home_page(runs=frozenset({TAGS_PATH, PEOPLE_PATH, MEANING_PATH})).decode()
    assert PEOPLE_PATH in both
    assert MEANING_PATH in both
    assert 'id="peopleDlg"' in both
