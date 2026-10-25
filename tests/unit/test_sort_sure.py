"""`review-sort`: which proposals are sure, and the batch that accepts them at once."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from media_hygiene.classify.models import Band
from media_hygiene.classify.page_decisions import PageDecisions, read_page_decisions
from media_hygiene.classify.page_overlay import overlay
from media_hygiene.classify.page_values import EventValue
from media_hygiene.classify.plan_file import PlanEvent
from media_hygiene.classify.workbook.edits import Edits, EventEdit, resolve
from media_hygiene.classify.worklist import work_list
from media_hygiene.errors import DecisionsError
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.review import sort_batch
from media_hygiene.review.sort_batch import SortBatchSession, SureBatch
from media_hygiene.review.sort_files import SortSource
from media_hygiene.review.sort_sure import reach, sure_value
from tests.support.plans import plan_of, row
from tests.support.sort_review import app_of, call

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow

SEA = "Mer"


def event(event_id: str, rows: list[PlanRow]) -> PlanEvent:
    """An event of these rows."""
    return PlanEvent(
        id=event_id,
        start="2016-07-14",
        end="2016-07-14",
        span="2016-07-14",
        label="",
        rows=tuple(item.id for item in rows),
    )


def members(key: str, sure: int, others: tuple[tuple[Band, str], ...]) -> list[PlanRow]:
    """`sure` rows of the sea, then rows in other bands and categories."""
    rows = [row(f"{key}{index}", Band.SURE, (SEA, key)) for index in range(sure)]
    rows += [
        row(f"{key}-{index}", band, (category, key))
        for index, (band, category) in enumerate(others)
    ]
    return rows


def make_plan() -> ClassifyPlan:
    """Four events, each a case.

    `sure`: sure, its photos to decide agree or say nothing; `mixed`: one proposes
    another category; `edited`: sure, but named in the workbook; `done`: nothing left
    to decide.
    """
    groups = {
        "sure": members("sure", 2, ((Band.UNSURE, SEA), (Band.MANUAL, ""))),
        "mixed": members("mixed", 2, ((Band.UNSURE, "Ski"),)),
        "edited": members("edited", 2, ((Band.UNSURE, SEA),)),
        "done": members("done", 1, ()),
    }
    rows = [item for group in groups.values() for item in group]
    return plan_of(rows, [event(key, group) for key, group in groups.items()])


def session_in(folder: Path) -> SortBatchSession:
    """A review of `make_plan`, the event `edited` named in the workbook."""
    plan = make_plan()
    workbook = Edits(events={"edited": EventEdit("Vacances")})
    target = folder / "sort-decisions.json"
    source = SortSource(plan, workbook, target, ("W", "D"), HostPathMapper(folder))
    return SortBatchSession(source, PageDecisions(plan_id=plan.plan_id))


def test_a_proposal_is_sure_when_its_photos_to_decide_agree() -> None:
    """Sure head, no other category, something left to decide."""
    found = {item.event.id: sure_value(item) for item in work_list(make_plan())}
    assert found == {
        "sure": EventValue(category=SEA),
        "mixed": None,
        "edited": EventValue(category=SEA),
        "done": None,
    }
    unsure = plan_of(
        [row("u", Band.UNSURE, (SEA, "x"))], [event("x", [row("u", Band.UNSURE)])]
    )
    assert sure_value(work_list(unsure)[0]) is None


def test_the_batch_is_one_write_read_back_then_taken_back(tmp_path: Path) -> None:
    """Only the open sure event is accepted; the file holds it; undo forgets it."""
    session = session_in(tmp_path)
    assert session.open_and_sure() == (2, 1)
    answer = session.batch(SureBatch(events=("sure", "mixed", "edited", "done", "x")))
    assert answer.changed == 1
    assert [card.id for card in answer.events] == ["sure"]
    assert answer.events[0].page is not None
    assert answer.size == (tmp_path / "sort-decisions.json").stat().st_size
    saved = read_page_decisions(tmp_path / "sort-decisions.json", "p")
    [decision] = saved.events
    assert (decision.event, decision.value, decision.base) == (
        "sure",
        EventValue(category=SEA),
        EventValue(),
    )
    folders = {
        item.row.id: item.folder
        for item in resolve(make_plan(), overlay(Edits(), saved).edits)
    }
    assert folders["sure-0"] == folders["sure-1"] == f"2016/{SEA}"
    assert session.open_and_sure() == (1, 0)
    with pytest.raises(DecisionsError, match="No sure proposal"):
        session.batch(SureBatch(events=("sure",)))
    undone = session.batch(SureBatch(events=("sure",), undo=True))
    assert (undone.changed, undone.events[0].page) == (1, None)
    assert not read_page_decisions(tmp_path / "sort-decisions.json", "p").events
    with pytest.raises(DecisionsError, match="Nothing to take back"):
        session.batch(SureBatch(events=("sure",), undo=True))


def test_undo_keeps_a_choice_made_since(tmp_path: Path) -> None:
    """An event chosen again after the batch is not the batch's any more."""
    session = session_in(tmp_path)
    session.batch(SureBatch(events=("sure",)))
    session.choose_event("sure", EventValue(name="Plage", category=SEA))
    with pytest.raises(DecisionsError):
        session.batch(SureBatch(events=("sure",), undo=True))
    [kept] = read_page_decisions(tmp_path / "sort-decisions.json", "p").events
    assert kept.value.name == "Plage"


def test_a_failed_write_changes_nothing(tmp_path: Path) -> None:
    """The folder is gone: the error goes up, the session keeps its choices."""
    session = session_in(tmp_path / "gone")
    with pytest.raises(OSError, match="gone"):
        session.batch(SureBatch(events=("sure",)))
    assert session.progress == (0, 0)


def test_the_route_answers_from_the_disk(tmp_path: Path) -> None:
    """`POST /api/sure`: the batch read back; a malformed body is refused."""
    app = app_of(session_in(tmp_path))

    async def batch() -> list[tuple[HTTPStatus, bytes]]:
        answers = [
            await call(app, "POST /api/sure", {"events": ["sure"]}),
            await call(app, "POST /api/sure", {"events": "sure", "extra": 1}),
            await call(app, "POST /api/sure", {"events": ["sure"]}),
        ]
        return [(answer.status, answer.body) for answer in answers]

    (accepted, body), (malformed, _), (again, refusal) = asyncio.run(batch())
    assert (accepted, malformed, again) == (HTTPStatus.OK, 422, 422)
    assert json.loads(body)["events"][0]["sure"]
    assert "No sure proposal" in json.loads(refusal)["error"]


def test_a_file_that_does_not_hold_the_batch_is_said(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Read back without the batch (a sync tool put an old copy back): refused."""
    session = session_in(tmp_path)
    monkeypatch.setattr(
        sort_batch,
        "read_page_decisions",
        lambda _path, plan_id: PageDecisions(plan_id=plan_id),
    )
    with pytest.raises(DecisionsError, match="does not hold the 1 choices"):
        session.batch(SureBatch(events=("sure",)))


def test_the_batch_moves_only_the_loose_files_of_a_trip() -> None:
    """0385: the user's folders keep their files; the page counts what moves."""
    rows = [
        row("budva", Band.SURE, ("Montenegro/Budva", "trip")),
        *(
            row(name, Band.SURE, ("Photos Chloé", "trip")).model_copy(
                update={"path": f"C:\\Photos\\2016\\Photos Chloé\\{name}.jpg"}
            )
            for name in ("chloe", "chloe2")
        ),
        row("loose", Band.MANUAL, ("", "trip")),
    ]
    plan = plan_of(rows, (event("trip", rows),))
    item = work_list(plan)[0]
    value = sure_value(item)
    assert value == EventValue(category="Photos Chloé")
    effect = reach(item)
    assert (effect.moves, effect.kept, effect.folders) == (1, 1, ("Budva",))
    accepted = Edits(events={"trip": EventEdit("", value.category)})
    found = {d.row.id: d.folder for d in resolve(plan, accepted)}
    assert found == {
        "budva": "2016/Montenegro/Budva",
        "chloe": "2016/Photos Chloé",
        "chloe2": "2016/Photos Chloé",
        "loose": "2016/Photos Chloé",
    }
