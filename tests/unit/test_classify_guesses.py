"""A file `sort` put in "To check/<guess>" stays there, unless a rule is sure."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime

from media_hygiene.classify.bands import band_folders
from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.models import Band, SortReason
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.classify_settings import ClassifySettings
from tests.unit.test_classify_engine import ROOT, by_name, shot

SUMMER = datetime(2019, 7, 3, 10)
GUESSED = "2019/To check/Vacances"
SETTINGS = ClassifySettings()


def test_a_guess_sorted_to_check_stays_there_to_check() -> None:
    """No sure rule: in place, still to check, its category the folder's."""
    files = [
        shot(f"{GUESSED}/a.jpg", SUMMER),
        shot("2019/À vérifier/Mer/b.jpg", SUMMER),
    ]
    found = by_name(classify(files, SETTINGS, Scope()).proposals)
    for name, category in (("a.jpg", "Vacances"), ("b.jpg", "Mer")):
        proposal = found[name]
        assert proposal.in_place
        assert proposal.band is Band.UNSURE
        assert proposal.reason is SortReason.PREVIOUS_GUESS
        assert proposal.category == category


def test_a_sure_rule_still_takes_a_file_out_of_to_check() -> None:
    """A path rule reaching `sure` moves it where the rule says."""
    rule = ClassifyRule(
        name="Holidays", match=RuleMatch.PATH, pattern="Vacances", category="Holidays"
    )
    settings = ClassifySettings(rules=(rule,))
    (proposal,) = classify(
        [shot(f"{GUESSED}/a.jpg", SUMMER)], settings, Scope()
    ).proposals
    assert proposal.band is Band.SURE
    assert proposal.target == ROOT / "2019" / "Holidays"


def test_the_to_check_folder_of_a_custom_layout_is_a_guess_too() -> None:
    """`unsure_layout = "{year}/Unsure/{category}"`: `Unsure` holds guesses."""
    settings = ClassifySettings(unsure_layout="{year}/Unsure/{category}")
    every, unsure = band_folders(settings)
    assert "Unsure" in every
    assert unsure == ("Unsure",)
    rules = FolderRules.build((), (every, unsure))
    assert rules.guess(ROOT / "2019/Unsure/Beach", ROOT) == "Beach"
    assert rules.guess(ROOT / "2019/Unsure", ROOT) is None
    assert rules.guess(ROOT / "2019/Beach", ROOT) is None
    assert not rules.meaning(ROOT / "2019/Unsure/Beach", ROOT)
