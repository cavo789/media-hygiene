"""What `people` says: undecodable photos, Ctrl+C, the estimate, --sample, decimals."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.config.people_settings import PeopleSettings
from media_hygiene.console.people_view import (
    show_estimate,
    show_found,
    show_groups,
    show_missing,
)
from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from media_hygiene.index.face_rows import FaceTally
from media_hygiene.services.people_find import FindOutcome, workers
from media_hygiene.services.people_groups import PeopleGroups
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_undecodable_photos_and_ctrl_c_are_said(locations: Locations) -> None:
    """Nothing analysed: no success line, the undecodable count, how to go on."""
    runtime = make_runtime(locations)
    show_missing(runtime.output, 0, 10)
    show_found(runtime.output, FindOutcome(unreadable=2, stopped=True))
    printed = " ".join(output_of(runtime).split())
    assert "analysed" not in printed
    assert "to analyse" not in printed
    assert "2 photos could not be decoded." in printed
    assert "the next people run goes on where this one stopped" in printed


def test_the_estimate_follows_the_pace_and_the_workers() -> None:
    """Nothing analysed: no estimate; otherwise seconds per photo, shared."""
    assert FindOutcome().estimate(100) == 0.0
    outcome = FindOutcome(seconds=4.0, analysed=4)
    assert outcome.estimate(10 * workers()) == 10.0


def test_french_decimals_and_a_single_group(locations: Locations) -> None:
    """The seconds and the sharpness take the French separator; one group, its size."""
    install(Locale.FR)
    runtime = make_runtime(locations)
    show_found(runtime.output, FindOutcome(seconds=0.5, analysed=4, faces=3))
    groups = PeopleGroups((), too_small=1, too_blurry=2)
    settings = PeopleSettings(min_sharpness=12.5)
    show_groups(runtime.output, groups, (FaceTally(4, 3, 0.1), settings))
    printed = " ".join(output_of(runtime).split())
    assert "0,12 s par photo" in printed
    assert "plus flous que 12,5" in printed
    assert "aucun ne ressemble assez à un autre pour être regroupé" in printed


def test_a_sample_says_no_page_opens(locations: Locations) -> None:
    """`--sample` measures only: it says so, with or without photos left."""
    runtime = make_runtime(locations)
    show_estimate(runtime.output, 0, 0.0)
    show_estimate(runtime.output, 40, 12.0)
    printed = " ".join(output_of(runtime).split())
    assert printed.count("--sample only measures: no page opens.") == 2
    assert "40 more photos" in printed
