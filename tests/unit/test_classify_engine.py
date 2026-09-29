"""One proposal per file: folders, events, bands, layouts, and nothing moves twice."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.models import Band, MediaInput, Proposal, SortReason
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.scan.models import VisualFacts

ROOT = Path("/data/c/Photos")
SETTINGS = ClassifySettings()


def shot(
    relative: str, when: datetime | None, camera: str | None = "Pixel"
) -> MediaInput:
    """A photo with an EXIF date (none: only its mtime)."""
    taken = when.strftime("%Y:%m:%d %H:%M:%S") if when else None
    visual = VisualFacts(0, 0, 1, 1, 0.0, taken, camera)
    return MediaInput(ROOT / relative, ROOT, 10, 0, visual)


def series(folder: str, start: datetime, count: int) -> list[MediaInput]:
    """`count` photos in `folder`, one hour apart."""
    return [
        shot(f"{folder}/{index}.jpg", start + timedelta(hours=index))
        for index in range(count)
    ]


def by_name(proposals: tuple[Proposal, ...]) -> dict[str, Proposal]:
    """Proposals by file name."""
    return {proposal.file.path.name: proposal for proposal in proposals}


def test_a_meaningful_folder_is_kept_under_its_year_and_stays_in_place() -> None:
    """`2019/Seaside` stays; `Juillet 2016 - Vacances` becomes `2016/Vacances`."""
    july = datetime(2016, 7, 3, 10)
    files = [
        shot("2019/Seaside/a.jpg", datetime(2019, 8, 1, 10)),
        shot("Juillet 2016 - Vacances/b.jpg", july),
    ]
    found = by_name(classify(files, SETTINGS, Scope()).proposals)
    assert found["a.jpg"].reason is SortReason.EXISTING_FOLDER
    assert found["a.jpg"].in_place
    assert found["b.jpg"].target == ROOT / "2016" / "Vacances"
    assert found["b.jpg"].band is Band.SURE


def test_loose_files_go_to_sort_and_stay_there_the_next_time() -> None:
    """Idempotence: a file already in its "to sort" folder is in place."""
    first = classify(
        [shot("2019/Juillet 2019/a.jpg", datetime(2019, 7, 1))], SETTINGS, Scope()
    )
    (proposal,) = first.proposals
    assert proposal.band is Band.MANUAL
    assert proposal.folder == "2019/To sort/2019-07"
    moved = shot("2019/To sort/2019-07/a.jpg", datetime(2019, 7, 1))
    (again,) = classify([moved], SETTINGS, Scope()).proposals
    assert again.in_place


def test_without_category_in_the_layout_a_date_is_enough() -> None:
    """`{year}/{month}` sorts loose files for sure, with no taxonomy."""
    settings = ClassifySettings(layout="{year}/{month}")
    (proposal,) = classify(
        [shot("DCIM/a.jpg", datetime(2019, 7, 1))], settings, Scope()
    ).proposals
    assert (proposal.band, proposal.reason, proposal.folder) == (
        Band.SURE,
        SortReason.DATE_ONLY,
        "2019/07",
    )


def test_an_evening_and_the_next_morning_are_one_event() -> None:
    """Sessions 12 hours apart join; 3 photos are no event, only a month."""
    evening = series("DCIM", datetime(2016, 7, 14, 18), 3)
    morning = series("Camera", datetime(2016, 7, 15, 8), 3)
    alone = series("DCIM/100CANON", datetime(2016, 9, 1, 10), 3)
    result = classify([*evening, *morning, *alone], SETTINGS, Scope())
    (event,) = result.events
    assert len(event.paths) == 6
    found = {p.file.path: p for p in result.proposals}
    assert found[evening[0].path].folder == "2016/To sort/2016-07-14..07-15"
    assert found[alone[0].path].folder == "2016/To sort/2016-09"


def test_a_new_year_party_stays_in_one_year() -> None:
    """The event takes the year of its start."""
    party = series("DCIM", datetime(2016, 12, 31, 22), 5)
    folders = {p.folder for p in classify(party, SETTINGS, Scope()).proposals}
    assert folders == {"2016/To sort/2016-12-31..2017-01-01"}


def test_loose_files_of_an_event_join_its_meaningful_folder() -> None:
    """One phone saved the party in `Anniversaire Léa`, the other in `DCIM`."""
    start = datetime(2018, 3, 12, 14)
    named = series("Anniversaire Léa", start, 3)
    loose = [
        shot(f"DCIM/{i}.jpg", start + timedelta(minutes=30 * i + 5)) for i in range(3)
    ]
    found = {
        p.file.path: p for p in classify([*named, *loose], SETTINGS, Scope()).proposals
    }
    joined = found[loose[0].path]
    assert (joined.reason, joined.category) == (
        SortReason.EVENT_NEIGHBOUR,
        "Anniversaire Léa",
    )
    assert joined.band is Band.UNSURE
    assert joined.folder == "2018/To check/Anniversaire Léa"


def test_undated_files_are_split_by_camera_trace() -> None:
    """A shot with a lost date, or a picture received."""
    files = [shot("x/a.jpg", None), shot("x/b.jpg", None, camera=None)]
    found = by_name(classify(files, SETTINGS, Scope()).proposals)
    assert found["a.jpg"].folder == "To sort/Undated"
    assert found["b.jpg"].folder == "To sort/Received and downloaded"
    assert found["b.jpg"].band is Band.UNDATED


def test_kept_folders_and_empty_layouts_stay_where_they_are() -> None:
    """Protected or `leave` folders never move; an empty layout means stay."""
    files = [
        shot("Albums/a.jpg", datetime(2019, 7, 1)),
        shot("DCIM/b.jpg", datetime(2019, 7, 1)),
    ]
    settings = ClassifySettings(manual_layout="")
    found = by_name(classify(files, settings, Scope(kept=(ROOT / "Albums",))).proposals)
    assert found["a.jpg"].band is Band.STAY
    assert found["b.jpg"].folder is None
    assert all(proposal.in_place for proposal in found.values())


def test_a_target_and_a_year_scope() -> None:
    """A separate target receives the tree; `--year` limits the proposals."""
    files = [
        shot("2019/Sea/a.jpg", datetime(2019, 8, 1)),
        shot("2020/Sea/b.jpg", datetime(2020, 8, 1)),
    ]
    target = Path("/data/d/Tri")
    result = classify(files, SETTINGS, Scope(target=target, years=(2019, 2019)))
    (proposal,) = result.proposals
    assert proposal.target == target / "2019" / "Sea"
