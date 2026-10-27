"""Search by meaning built by the home page (0425): figures, Stop, resume; opt-in."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from media_hygiene.cli import home_meaning
from media_hygiene.cli.home_meaning import page_meaning
from media_hygiene.meaning.files import clip_known
from media_hygiene.services.home_tags import HomeTags
from media_hygiene.services.home_tags_models import TagsPhase, TagsRunner
from tests.integration.tags.test_tags_meaning import PHOTOS, _vectors
from tests.support.meaning import ColourImages
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.console.page_progress import PageProgress
    from media_hygiene.paths.locations import Locations

_POLL = 0.01
_FIRST = 3


def _wait(run: HomeTags) -> None:
    """Wait for the half running to end, as the page polls."""
    while run.state().phase in {TagsPhase.PREPARING, TagsPhase.RUNNING}:
        time.sleep(_POLL)


def _ran(run: HomeTags, minutes: int | None = None) -> HomeTags:
    """Prepare, then look; both halves waited for."""
    assert run.prepare()
    _wait(run)
    assert run.state().phase is TagsPhase.ASKING, run.state().error
    assert run.describe(minutes)
    _wait(run)
    return run


def test_the_page_builds_search_by_meaning_and_resumes(
    cli: CliRunner,
    locations: Locations,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Figures first, never the model; a stop keeps the vectors; the next run ends."""
    del cli
    model: list[Path] = []
    monkeypatch.setenv("MEDIA_HYGIENE_TAGS__MEANING", "true")
    monkeypatch.setattr(home_meaning, "clip_files", lambda cache: _loaded(model, cache))
    monkeypatch.setattr(home_meaning, "ClipImages", ColourImages)
    runtime = make_runtime(locations)
    real = page_meaning(runtime)
    asked: list[int] = []

    def some(progress: PageProgress, stopped: Callable[[], bool]) -> tuple[str, ...]:
        """The real half, stopped after a few photos as by Stop."""
        return real.describe(progress, lambda: stopped() or _count(asked) > _FIRST)

    first = HomeTags(TagsRunner(real.prepare, some))
    assert first.prepare()
    _wait(first)
    figures = first.state().figures
    assert figures is not None
    assert figures.to_describe == PHOTOS
    assert not model  # the figures never load the model
    _ran(first)
    assert first.state().phase is TagsPhase.DONE, first.state().error
    assert _vectors(locations) == _FIRST
    whole = _ran(HomeTags(real))
    assert whole.state().phase is TagsPhase.DONE, whole.state().error
    assert _vectors(locations) == PHOTOS
    assert "can now be found" in whole.state().lines[0]


def test_off_is_one_line(cli: CliRunner, locations: Locations) -> None:
    """`[tags] meaning` off: the page says how to turn it on."""
    del cli
    run = HomeTags(page_meaning(make_runtime(locations)))
    assert run.prepare()
    _wait(run)
    state = run.state()
    assert state.phase is TagsPhase.FAILED
    assert "meaning = true" in (state.error or "")


def _count(asked: list[int]) -> int:
    """Count one more question "stop now?"."""
    asked.append(0)
    return len(asked)


def _loaded(model: list[Path], cache: Path) -> object:
    """The model's files, "downloaded" when asked.

    Returns:
        Where they are.
    """
    model.append(cache)
    return clip_known(cache)
