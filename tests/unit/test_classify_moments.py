"""0386: a person's photos join the user's folder of the same moment, else the trip."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.models import Band, MediaInput, SortReason
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from tests.support.layouts import legacy
from tests.unit.test_classify_engine import ROOT, by_name, shot

if TYPE_CHECKING:
    from media_hygiene.classify.models import Proposal
    from media_hygiene.config.classify_settings import ClassifySettings

SETTINGS = legacy()
CHLOE = Scope(people=("Chloé",))


def day(folder: str, when: tuple[int, ...]) -> list[MediaInput]:
    """Photos of July 2019 in `folder`: (day, hour) after (day, hour)."""
    pairs = zip(when[::2], when[1::2], strict=True)
    return [
        shot(
            f"{folder}/{folder.rsplit('/', 1)[-1]}-{d}-{h}.jpg", datetime(2019, 7, d, h)
        )
        for d, h in pairs
    ]


def trip() -> list[MediaInput]:
    """Three named folders over three days, one session a day, one event."""
    return [
        *day("2019/Montenegro/Budva", (12, 10, 12, 12, 12, 14, 12, 16)),
        *day("2019/Montenegro/Cetinje", (13, 9, 13, 11, 13, 13, 13, 15)),
        *day("2019/Montenegro/Lovcen", (14, 8, 14, 10, 14, 12, 14, 14)),
    ]


def test_an_event_keeps_its_sessions() -> None:
    """A night cuts the sessions, not the event."""
    (event,) = classify(trip(), SETTINGS, Scope()).events
    assert [len(session) for session in event.sessions] == [4, 4, 4]


def test_a_persons_photos_join_the_folder_of_their_session() -> None:
    """Each day's photo joins that day's folder; the one of no session, the trip's."""
    chloe = day("2019/Photos Chloé", (12, 11, 13, 12, 13, 23, 14, 11))
    manon = [shot("Manon 2023/dcim/m.jpg", datetime(2019, 7, 14, 9))]
    found = by_name(classify([*trip(), *chloe, *manon], SETTINGS, CHLOE).proposals)
    expected = {
        "Photos Chloé-12-11.jpg": "Montenegro/Budva",
        "Photos Chloé-13-12.jpg": "Montenegro/Cetinje",
        "Photos Chloé-14-11.jpg": "Montenegro/Lovcen",
        "Photos Chloé-13-23.jpg": "Montenegro",
        "m.jpg": "Montenegro/Lovcen",
    }
    for name, category in expected.items():
        proposal = found[name]
        assert proposal.reason is SortReason.SAME_MOMENT, name
        assert proposal.values is not None
        assert proposal.values.category == category, name
        assert proposal.band is Band.UNSURE
    assert found["Budva-12-10.jpg"].reason is SortReason.EXISTING_FOLDER
    assert found["Budva-12-10.jpg"].in_place


def test_the_nearest_folder_in_time_wins_within_a_session() -> None:
    """Two named folders in one session: the photo goes to the closer one."""
    files = [
        *day("2019/Plage", (12, 10, 12, 11, 12, 12)),
        *day("2019/Port", (12, 15, 12, 16, 12, 17)),
        *day("2019/Photos Chloé", (12, 11, 12, 16)),
    ]
    found = by_name(classify(files, SETTINGS, CHLOE).proposals)
    assert found["Photos Chloé-12-11.jpg"].values.category == "Plage"  # type: ignore[union-attr]
    assert found["Photos Chloé-12-16.jpg"].values.category == "Port"  # type: ignore[union-attr]


def test_one_named_folder_works_as_event_neighbours_do() -> None:
    """Loose files stay event neighbours; a person's photo joins the folder too."""
    files = [
        *day("2019/Montenegro/Budva", (12, 10, 12, 12, 12, 14, 12, 16)),
        shot("DCIM/loose.jpg", datetime(2019, 7, 12, 11)),
        shot("2019/Photos Chloé/c.jpg", datetime(2019, 7, 12, 23)),
    ]
    found = by_name(classify(files, SETTINGS, CHLOE).proposals)
    assert found["loose.jpg"].reason is SortReason.EVENT_NEIGHBOUR
    assert found["c.jpg"].reason is SortReason.SAME_MOMENT
    assert found["c.jpg"].values.category == "Montenegro/Budva"  # type: ignore[union-attr]


def test_the_rule_turned_off_gives_todays_proposals() -> None:
    """`same-moment = 0`: the person's folder is its own category again."""
    settings = legacy(scores={"same-moment": 0})
    chloe = day("2019/Photos Chloé", (12, 11))
    found = by_name(classify([*trip(), *chloe], settings, CHLOE).proposals)
    proposal = found["Photos Chloé-12-11.jpg"]
    assert proposal.reason is SortReason.PERSON_FOLDER
    assert proposal.values is not None
    assert proposal.values.category == "Photos Chloé"


def test_a_folder_is_a_persons_when_it_holds_their_name() -> None:
    """`person_folders`, as a word, case and accents ignored; not a part of a word."""
    settings = legacy(person_folders=("chloe",))
    files = [
        shot("2019/PHOTOS CHLOÉ/a.jpg", datetime(2019, 3, 1, 10)),
        shot("2019/Chloéville/b.jpg", datetime(2019, 4, 1, 10)),
    ]
    found = by_name(classify(files, settings, Scope()).proposals)
    assert found["a.jpg"].reason is SortReason.PERSON_FOLDER
    assert found["b.jpg"].reason is SortReason.EXISTING_FOLDER
    unnamed = by_name(classify(files, SETTINGS, Scope()).proposals)
    assert unnamed["a.jpg"].reason is SortReason.EXISTING_FOLDER


def test_a_trip_folder_is_never_a_generic_one() -> None:
    """Folders sharing no parent: a photo of no session keeps today's proposal."""
    files = [
        *day("2019/Budva", (12, 10, 12, 12, 12, 14, 12, 16)),
        *day("2019/Cetinje", (13, 9, 13, 11, 13, 13, 13, 15)),
        shot("2019/Photos Chloé/c.jpg", datetime(2019, 7, 12, 23)),
    ]
    found = by_name(classify(files, SETTINGS, CHLOE).proposals)
    assert found["c.jpg"].reason is SortReason.PERSON_FOLDER
    assert found["c.jpg"].target == ROOT / "2019" / "Photos Chloé"


# 0391: a rule's category becomes the parent of the folders the user named.
TRIP_RULE = ClassifyRule(
    name="Montenegro",
    match=RuleMatch.DATE_RANGE,
    dates="2019-07-12..2019-07-14",
    category="Vacances et sorties/Montenegro",
    keep_folders=True,
)


def with_rule(rule: ClassifyRule) -> ClassifySettings:
    """The default settings, a rule written above them."""
    return legacy(rules=(rule, *legacy().rules))


def categories(found: dict[str, Proposal], names: tuple[str, ...]) -> list[str]:
    """The category proposed for each file named."""
    return [found[name].values.category for name in names]  # type: ignore[union-attr]


def test_a_rule_keeping_folders_puts_them_below_its_category() -> None:
    """Budva, Cetinje stay below the rule's folder; the daughters' photos follow."""
    chloe = day("2019/Photos Chloé", (12, 11, 13, 23))
    run = classify([*trip(), *chloe], with_rule(TRIP_RULE), CHLOE)
    found = by_name(run.proposals)
    trip_folder = "Vacances et sorties/Montenegro"
    assert categories(
        found, ("Budva-12-10.jpg", "Cetinje-13-9.jpg", "Lovcen-14-8.jpg")
    ) == [
        f"{trip_folder}/Budva",
        f"{trip_folder}/Cetinje",
        f"{trip_folder}/Lovcen",
    ]
    assert categories(found, ("Photos Chloé-12-11.jpg",)) == [f"{trip_folder}/Budva"]
    assert categories(found, ("Photos Chloé-13-23.jpg",)) == [trip_folder]
    assert found["Budva-12-10.jpg"].rule == "Montenegro"
    assert found["Budva-12-10.jpg"].band is Band.SURE
    assert found["Budva-12-10.jpg"].target == (
        ROOT / "2019" / "Vacances et sorties" / "Montenegro" / "Budva"
    )


def test_without_keep_folders_the_rule_puts_the_trip_flat() -> None:
    """Today's rule: every photo of the dates in its one folder."""
    flat = TRIP_RULE.model_copy(update={"keep_folders": False})
    found = by_name(classify(trip(), with_rule(flat), Scope()).proposals)
    assert set(categories(found, ("Budva-12-10.jpg", "Cetinje-13-9.jpg"))) == {
        "Vacances et sorties/Montenegro"
    }


def test_one_named_folder_becomes_the_rule_category() -> None:
    """No `Montenegro/Budva` below: the one folder is the rule's category."""
    files = [
        *day("2019/Montenegro/Budva", (12, 10, 12, 12, 12, 14, 12, 16)),
        shot("DCIM/loose.jpg", datetime(2019, 7, 12, 11)),
    ]
    found = by_name(classify(files, with_rule(TRIP_RULE), Scope()).proposals)
    assert set(categories(found, ("Budva-12-10.jpg", "loose.jpg"))) == {
        "Vacances et sorties/Montenegro"
    }


def test_keep_folders_needs_a_category() -> None:
    """Nothing to keep the folders below: refused, the rule named."""
    with pytest.raises(ValueError, match="Montenegro"):
        ClassifyRule(
            name="Montenegro",
            match=RuleMatch.DATE_RANGE,
            dates="2019-07-12..2019-07-14",
            keep_folders=True,
        )


# 0394: the main folder is the rule's folder; screenshots are never a date rule's.
WEDDING_RULE = ClassifyRule(
    name="Mariage d'Hervé et Magda",
    match=RuleMatch.DATE_RANGE,
    dates="2017-08-05..2017-08-06",
    category="Fêtes/Mariages/Mariage d'Hervé et Magda",
    keep_folders=True,
)
WEDDING = "Fêtes/Mariages/Mariage d'Hervé et Magda"


def wedding() -> list[MediaInput]:
    """14 in the wedding's folder, 3 of Manon, 2 screenshots, 1 in an unrelated one."""
    folder = "2017/Août 2017/Mariage Hervé et Magda"
    return [
        *(
            shot(f"{folder}/w{index}.jpg", datetime(2017, 8, 5, 15 + index // 2))
            for index in range(14)
        ),
        *(
            shot(f"Manon/2017/m{hour}.jpg", datetime(2017, 8, 5, hour, 30))
            for hour in (16, 18, 20)
        ),
        shot("Screenpresso/s1.png", datetime(2017, 8, 6, 10, 32), camera=None),
        shot("Screenpresso/Thumbnails/s2.png", datetime(2017, 8, 6, 16, 57), None),
        shot("2017/Développement Sep/d.jpg", datetime(2017, 8, 5, 19, 10)),
    ]


def test_the_main_folder_is_the_rules_folder() -> None:
    """The wedding in the category itself; Manon's joins it; screenshots stay apart."""
    settings = with_rule(WEDDING_RULE).model_copy(update={"person_folders": ("Manon",)})
    found = by_name(classify(wedding(), settings, Scope()).proposals)
    assert set(categories(found, ("w0.jpg", "w13.jpg", "m16.jpg", "m20.jpg"))) == {
        WEDDING
    }
    assert found["w0.jpg"].target == ROOT / "2017" / "Fêtes" / "Mariages" / (
        "Mariage d'Hervé et Magda"
    )
    assert categories(found, ("d.jpg",)) == ["Développement Sep"]  # another moment's
    alone = by_name(classify(wedding(), SETTINGS, Scope()).proposals)
    for name in ("s1.png", "s2.png"):
        assert found[name].rule == alone[name].rule != WEDDING_RULE.name, name
        assert found[name].target == alone[name].target, name


def test_a_folder_named_after_another_moment_is_not_taken() -> None:
    """Manon's photos join the wedding; `Développement Sep` (named, one moment) stays.

    0404, decided with the maintainer (2026-10-25): a date rule takes no file of a
    folder the user named after another event; the event's main folder is the rule's.
    """
    found = by_name(classify(wedding(), with_rule(WEDDING_RULE), Scope()).proposals)
    assert set(categories(found, ("w0.jpg", "m16.jpg"))) == {WEDDING}
    assert found["d.jpg"].rule == "Existing folders"
    assert categories(found, ("d.jpg",)) == ["Développement Sep"]
    assert found["s1.png"].rule != WEDDING_RULE.name


def test_a_screenshot_is_never_taken_by_a_date_rule_listed_first() -> None:
    """The `kind` rule listed below the date rule still keeps its screenshots."""
    flat = WEDDING_RULE.model_copy(update={"keep_folders": False})
    loose = [shot("DCIM/Screenshot_20170806.png", datetime(2017, 8, 6, 9), None)]
    files = [*wedding(), *loose]
    found = by_name(classify(files, with_rule(flat), Scope()).proposals)
    assert found["w0.jpg"].rule == flat.name
    assert found["Screenshot_20170806.png"].rule == "Screenshots and documents"
