"""0386: a person's photos join the user's folder of the same moment, else the trip."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.models import Band, MediaInput, SortReason
from media_hygiene.config.classify_settings import ClassifySettings
from tests.unit.test_classify_engine import ROOT, by_name, shot

SETTINGS = ClassifySettings()
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
    settings = ClassifySettings(scores={"same-moment": 0})
    chloe = day("2019/Photos Chloé", (12, 11))
    found = by_name(classify([*trip(), *chloe], settings, CHLOE).proposals)
    proposal = found["Photos Chloé-12-11.jpg"]
    assert proposal.reason is SortReason.PERSON_FOLDER
    assert proposal.values is not None
    assert proposal.values.category == "Photos Chloé"


def test_a_folder_is_a_persons_when_it_holds_their_name() -> None:
    """`person_folders`, as a word, case and accents ignored; not a part of a word."""
    settings = ClassifySettings(person_folders=("chloe",))
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
