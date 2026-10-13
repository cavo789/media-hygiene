"""`folder_town`: a folder named after a town, and the user's names for the towns."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.models import Band, MediaInput, SortReason
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import VisualFacts
from tests.support.located import HOME, ROOT, TRIP_RULE, TURIN, outing, start_of
from tests.support.towns import write_towns

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.models import Proposal

FOLDER_TOWN = ClassifyRule(name="Towns", match=RuleMatch.FOLDER_TOWN)
LIEGE = (50.6326, 5.5797)  # Belgium, 20 km from Durbuy


@pytest.fixture(name="towns")
def towns_fixture(tmp_path: Path) -> Gazetteer:
    """The tiny snapshot."""
    return Gazetteer.load(write_towns(tmp_path))


def shots(folder: str, where: tuple[float, float] | None = None) -> list[MediaInput]:
    """Five photos of one day in `folder` (below the root), maybe located."""
    visual = VisualFacts(0, 0, 4000, 3000, 0.0, "2017:07:14 10:00:00", "Phone")
    metadata = MediaMetadata(latitude=where[0], longitude=where[1]) if where else None
    return [
        MediaInput(ROOT / folder / f"IMG_{n}.jpg", ROOT, 10, 0, visual, metadata)
        for n in range(5)
    ]


def run(files: list[MediaInput], towns: Gazetteer, **more: object) -> list[Proposal]:
    """Classify with the folder-town rule only (home in Belgium)."""
    settings = ClassifySettings.model_validate(
        {"rules": (FOLDER_TOWN,), "places": (HOME,), **more}
    )
    return list(classify(files, settings, Scope(towns=towns)).proposals)


def test_a_folder_named_after_a_town_is_a_place_to_check(towns: Gazetteer) -> None:
    """`2017/Durbuy` → Belgium/Durbuy, to check (score 60); accents do not matter."""
    found = run(shots("2017/Durbuy") + shots("2018/DÜRBUY/Jour 1"), towns)
    assert {p.category for p in found} == {"Belgium/Durbuy"}
    assert {(p.reason, p.band) for p in found} == {
        (SortReason.FOLDER_TOWN, Band.UNSURE)
    }


def test_a_word_or_a_small_town_names_nothing(towns: Gazetteer) -> None:
    """`Vacances`, a town's name inside a longer one, a 3,000-inhabitant town, `Mai`."""
    files = shots("Vacances") + shots("Durbuy 2017") + shots("2019/Stoumont")
    files += shots("2019/Mai")  # Mai, Kenya in the real snapshot: a month here
    assert {p.reason for p in run(files, towns)} == {SortReason.NO_SIGNAL}
    lower = run(shots("2019/Stoumont"), towns, folder_town_min_population=1000)
    assert {p.category for p in lower} == {"Belgium/Stoumont"}


def test_photos_located_elsewhere_overrule_the_folder(towns: Gazetteer) -> None:
    """A `Nice` folder whose photos lie in Belgium: not Nice."""
    assert {p.reason for p in run(shots("Nice", LIEGE), towns)} == {
        SortReason.NO_SIGNAL
    }
    assert {p.category for p in run(shots("Nice"), towns)} == {"France/Nice"}


def test_homonyms_prefer_the_countries_of_the_collection(towns: Gazetteer) -> None:
    """Bruges: the Belgian one (home's country) over the one in Gironde."""
    found = run(shots("Bruges"), towns)
    assert {(p.category, p.file.path.parent.name) for p in found} == {
        ("Belgium/Bruges", "Bruges")
    }


def test_the_users_names_rename_and_find_the_towns(towns: Gazetteer) -> None:
    """`Turin` = `Torino`: the trip, `{city}` and a `Torino` folder all use it."""
    renamed = towns.renamed({"Turin": "Torino", "Unknown town": "Nowhere"})
    city = ClassifyRule(name="City", match=RuleMatch.TRIP, category="Trips/{city}")
    settings = ClassifySettings(rules=(TRIP_RULE,), places=(HOME,))
    trip = outing("t", start_of(3), (TURIN,) * 5)
    found = classify(trip, settings, Scope(towns=renamed)).proposals
    assert {p.category for p in found} == {"Italy/Torino"}
    settings = ClassifySettings(rules=(city,), places=(HOME,))
    found = classify(trip, settings, Scope(towns=renamed)).proposals
    assert {p.category for p in found} == {"Trips/Torino"}
    folders = shots("Torino") + shots("Turin")
    assert {p.category for p in run(folders, renamed)} == {"Italy/Torino"}
    assert renamed.search("torino", 1)[0].name == "Torino"
    assert towns.town(0).name == renamed.town(0).name  # the original is untouched


def test_town_names_must_not_be_empty() -> None:
    """`"Brugge" = ""` is refused when the configuration is read."""
    with pytest.raises(ValidationError):
        ClassifySettings.model_validate({"town_names": {"Brugge": " "}})
    names = ClassifySettings.model_validate({"town_names": {" Brugge ": "Bruges"}})
    assert names.town_names == {"Brugge": "Bruges"}


def test_ignored_names_are_never_towns(towns: Gazetteer) -> None:
    """`folder_town_ignore`: a first name that is a town somewhere, any case."""
    ignored = run(shots("Nice"), towns, folder_town_ignore=("NICE",))
    assert {p.reason for p in ignored} == {SortReason.NO_SIGNAL}
