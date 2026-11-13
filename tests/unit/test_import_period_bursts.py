"""0785: the period of a phone import on the home page, the bursts in the end line."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_hygiene.cli.menu_steps import full_catalog
from media_hygiene.report.burst_decisions import BurstDecision, BurstStatus
from media_hygiene.report.decisions import DecisionsFile
from media_hygiene.review.home_fields import FieldError, checked_words
from media_hygiene.services.import_bursts import IMPORT_DECISIONS
from media_hygiene.services.import_copies import reviewed_bursts, tell_done
from tests.support.runtime import make_locations, make_runtime, output_of


@pytest.mark.parametrize(
    ("period", "words"),
    [
        ("last", ("import", "--phone")),
        ("today", ("import", "--phone", "--since", "today")),
        ("week", ("import", "--phone", "--since", "week")),
        ("month", ("import", "--phone", "--since", "month")),
        ("all", ("import", "--phone", "--since", "all")),
    ],
)
def test_the_period_chosen_reaches_since(period: str, words: tuple[str, ...]) -> None:
    """*Since the last import* keeps the command as it was; the others add --since."""
    assert checked_words(full_catalog().step("phone"), {"period": period}) == words


def test_a_period_out_of_its_choices_is_refused() -> None:
    """Only the buttons' values run."""
    with pytest.raises(FieldError, match="not one of its choices"):
        checked_words(full_catalog().step("phone"), {"period": "2026-01-01"})


def test_mh_menu_still_runs_the_phone_import_as_it_is() -> None:
    """A choice field has a default: the step is not one to type yourself."""
    phone = full_catalog().step("phone")
    assert not phone.asks
    assert not phone.typed


def _decisions(tmp_path: Path) -> Path:
    path = tmp_path / IMPORT_DECISIONS
    decisions = DecisionsFile(
        version=1,
        roots=("C:\\",),
        bursts=(
            BurstDecision(kept=(r"C:\a.jpg",), discarded=(r"C:\b.jpg", r"C:\c.jpg")),
            BurstDecision(kept=(r"C:\d.jpg",), discarded=(r"C:\e.jpg",)),
            BurstDecision(status=BurstStatus.TODO, kept=(r"C:\f.jpg", r"C:\g.jpg")),
        ),
    )
    path.write_text(decisions.model_dump_json(), encoding="utf-8")
    return path


def test_the_series_seen_and_their_shots_set_aside_are_counted(tmp_path: Path) -> None:
    """A series not seen counts for nothing; no file, or a bad one: zeros."""
    assert reviewed_bursts(_decisions(tmp_path)) == (2, 3)
    assert reviewed_bursts(tmp_path / "none.json") == (0, 0)
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    assert reviewed_bursts(bad) == (0, 0)


def test_the_end_line_counts_the_bursts(tmp_path: Path) -> None:
    """The end line names the burst series seen and their shots set aside."""
    locations = make_locations(tmp_path)
    runtime = make_runtime(locations)
    tell_done(runtime, (Path("/data/c/x.jpg"), Path("/data/c/y.jpg")))
    _decisions(locations.reports_dir)
    tell_done(runtime, (Path("/data/c/x.jpg"),))
    text = " ".join(output_of(runtime).split())
    assert "2 new photos and videos in your library." in text
    assert "1 new photo or video in your library, 2 burst series reviewed" in text
    assert "(3 shots set aside)." in text
