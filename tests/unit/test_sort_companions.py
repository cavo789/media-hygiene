"""Companions: a file edit on any member decides for all; two that disagree refuse."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions.sort_build import PlanContext, sort_plan
from media_hygiene.classify.models import Band, DateSource, SortReason
from media_hygiene.classify.plan_file import PlanRow
from media_hygiene.classify.workbook.edits import Decision, Source
from media_hygiene.console.sort_view import show_follows
from media_hygiene.errors import WorkbookError
from media_hygiene.services.sort_guards import check_companions
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from media_hygiene.actions.sort_plan import SortPlan
    from media_hygiene.paths.locations import Locations

type Edit = tuple[str | None, Source]
PROPOSED = "2016/Juillet"


def decision(name: str, edit: Edit = (PROPOSED, Source.PROPOSAL)) -> Decision:
    """The decision of a file of the DCIM folder: its folder, where it comes from."""
    folder, source = edit
    row = PlanRow(
        id=name,
        path=f"C:\\Photos\\DCIM\\{name}",
        size=1,
        mtime_ns=0,
        sha256=None,
        date=None,
        date_source=DateSource.EXIF,
        event_id="e1",
        values=None,
        band=Band.UNSURE,
        reason=SortReason.EXISTING_FOLDER,
        score=50,
        root="C:\\Photos",
        folder=PROPOSED,
        name=name,
    )
    band = Band.UNSURE if source is Source.PROPOSAL else Band.SURE
    cell = f"Files!K{len(name)}" if source is Source.FILE else ""
    return Decision(row, folder, band, source, cell)


def planned(locations: Locations, *decisions: Decision) -> SortPlan:
    """The sort of these decisions."""
    context = PlanContext(make_runtime(locations).mapper)
    return sort_plan("p", decisions, context)


def targets(plan: SortPlan) -> dict[str, str]:
    """File name → the folder it goes to, below the root."""
    return {
        move.source.name: group.folder.relative_to(group.root).as_posix()
        for group in plan.groups
        for move in group.moves
    }


def test_a_file_edit_on_the_video_moves_the_photo_too(locations: Locations) -> None:
    """The Live Photo's video edited, the photo proposed elsewhere: both follow."""
    plan = planned(
        locations,
        decision("IMG_1.HEIC"),
        decision("IMG_1.MOV", ("Vacances", Source.FILE)),
    )
    assert targets(plan) == {"IMG_1.HEIC": "Vacances", "IMG_1.MOV": "Vacances"}
    assert {move.band for move in plan.moves} == {Band.SURE}
    check_companions(plan)  # no conflict


def test_a_file_edit_on_the_photo_still_wins(locations: Locations) -> None:
    """The photo edited, the video's own event edit ignored."""
    plan = planned(
        locations,
        decision("IMG_1.HEIC", ("Mer", Source.FILE)),
        decision("IMG_1.MOV", ("Fête", Source.GROUP)),
    )
    assert set(targets(plan).values()) == {"Mer"}
    assert not plan.companions.follows


def test_a_stay_edit_keeps_the_whole_group(locations: Locations) -> None:
    """A "(stay where it is)" on the RAW twin: the JPEG stays too."""
    plan = planned(
        locations,
        decision("IMG_2.JPG"),
        decision("IMG_2.CR2", (None, Source.FILE)),
    )
    assert not plan.groups
    assert plan.stay == 2


@pytest.mark.parametrize(
    ("photo", "video"), [("Mer", "Montagne"), ("Mer", None), (None, "Montagne")]
)
def test_two_disagreeing_file_edits_refuse_naming_both_cells(
    locations: Locations, photo: str | None, video: str | None
) -> None:
    """Different folders, or a folder and "stay": refused before anything moves."""
    plan = planned(
        locations,
        decision("IMG_1.HEIC", (photo, Source.FILE)),
        decision("IMG_1.MOV", (video, Source.FILE)),
        decision("IMG_1b.MOV", ("Ailleurs", Source.FILE)),  # another stem: alone
    )
    with pytest.raises(WorkbookError) as refused:
        check_companions(plan)
    message = refused.value.message
    assert "Files!K10 (IMG_1.HEIC)" in message
    assert "Files!K9 (IMG_1.MOV)" in message
    assert "IMG_1b.MOV" not in message
    assert "nothing was moved" in message


def test_equal_file_edits_are_no_conflict(locations: Locations) -> None:
    """The same folder typed on both rows: nothing to refuse."""
    plan = planned(
        locations,
        decision("IMG_1.HEIC", ("Mer", Source.FILE)),
        decision("IMG_1.MOV", ("Mer", Source.FILE)),
    )
    check_companions(plan)
    assert set(targets(plan).values()) == {"Mer"}


def test_event_edits_that_differ_the_first_one_wins_and_it_is_said(
    locations: Locations,
) -> None:
    """Two event edits: the leading file's wins; the other follows, one line."""
    plan = planned(
        locations,
        decision("IMG_1.MOV", ("Fête", Source.GROUP)),
        decision("IMG_1.HEIC", ("Mer", Source.GROUP)),
    )
    assert set(targets(plan).values()) == {"Mer"}
    assert plan.companions.follows == (("IMG_1.HEIC", ("IMG_1.MOV",)),)
    check_companions(plan)
    runtime = make_runtime(locations)
    show_follows(runtime.output, plan)
    assert "IMG_1.MOV follows IMG_1.HEIC" in output_of(runtime)


def test_an_event_edit_on_the_video_beats_the_photos_proposal(
    locations: Locations,
) -> None:
    """No file edit: an edit reaching any member comes before a proposal."""
    plan = planned(
        locations,
        decision("IMG_1.HEIC"),
        decision("IMG_1.MOV", ("Fête", Source.GROUP)),
    )
    assert set(targets(plan).values()) == {"Fête"}
    assert not plan.companions.follows  # the photo had no edit of its own
