"""A burst series set aside whole: every shot to the quarantine, `undo` restores."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from media_hygiene.report.decisions import read_decisions
from tests.integration.test_burst_review import shots, write_decisions
from tests.support.cli import run
from tests.support.review import (
    BURST_HOST,
    decide,
    review_session,
    serve_and_call,
    write_burst,
)

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

RAFALE = "c/Family Photos/Rafale"
SHOTS = [f"IMG_20{rank}.jpg" for rank in range(4)]


def test_the_page_sets_every_shot_aside(locations: Locations) -> None:
    """Saved with no kept shot, and resumed as such."""
    write_burst(locations.data_dir)
    [reply] = serve_and_call(review_session(locations), [decide(0, 0, 1, 2)])
    assert reply.status == 200
    [burst] = read_decisions(locations.reports_dir / "decisions.json").bursts
    assert burst.kept == ()
    assert burst.discarded == tuple(f"{BURST_HOST}\\IMG_{n}.jpg" for n in range(3))
    assert review_session(locations).state().series[0].discarded == (0, 1, 2)


def test_every_shot_goes_and_comes_back(cli: CliRunner, locations: Locations) -> None:
    """Counted in the summary; quarantined, never deleted; `undo` restores them."""
    write_decisions(locations, [], shots(0, 1, 2, 3))
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert "1 burst series is set aside whole" in result.output
    folder = locations.data_dir / RAFALE
    assert not any(folder.glob("*.jpg"))
    quarantined = sorted(p.name for p in locations.quarantine_dir.rglob("IMG_20*.jpg"))
    assert quarantined == SHOTS
    assert run(cli, "undo").exit_code == 0
    assert sorted(p.name for p in folder.glob("*.jpg")) == SHOTS


def test_a_shot_kept_for_its_copies_comes_back_with_them(
    cli: CliRunner, locations: Locations
) -> None:
    """A shot is also the kept copy of an exact duplicate: undo leaves all in place."""
    data = locations.data_dir
    copy = data / "d/backup/Rafale/IMG_200.jpg"
    copy.parent.mkdir(parents=True)
    shutil.copy2(data / RAFALE / SHOTS[0], copy)
    before = sorted(p.relative_to(data) for p in data.rglob("*") if p.is_file())
    write_decisions(locations, [], shots(0, 1, 2, 3))
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert not copy.exists()
    assert not (data / RAFALE / SHOTS[0]).exists()
    assert run(cli, "undo").exit_code == 0
    after = sorted(p.relative_to(data) for p in data.rglob("*") if p.is_file())
    assert after == before
