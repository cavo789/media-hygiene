"""The page's choices and the workbook's edits: one result, conflicts never silent."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import pytest

from media_hygiene.classify.carry_models import EditSheet, LostWhy
from media_hygiene.classify.workbook.edits import EventEdit
from media_hygiene.classify.workbook.reader import read_edits
from media_hygiene.errors import WorkbookError
from media_hygiene.services.sort_inputs import find_workbook, load_inputs
from tests.support.carrying import plan_of, run_classify
from tests.support.runtime import output_of
from tests.support.sort_review import call, classified, reopened
from tests.support.sorting import EVENT_NAME, PARTY, name_first_event, sort

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.sort_app import SortReviewApp
    from media_hygiene.services.runtime import Runtime

LATER = "Fancy fair"


def _name_here(app: SortReviewApp, name: str = EVENT_NAME) -> dict[str, object]:
    """Name the only event in the page.

    Args:
        app: The review.
        name: The name typed.

    Returns:
        The event's card, as the page receives it.
    """

    async def choose() -> dict[str, object]:
        [card] = json.loads((await call(app, "GET /api/state")).body)["events"]
        body = {"event": card["id"], "name": name}
        chosen: dict[str, object] = json.loads(
            (await call(app, "POST /api/event", body)).body
        )["card"]
        return chosen

    return asyncio.run(choose())


def _card(runtime: Runtime) -> dict[str, object]:
    """The only event, as a page reopened now shows it.

    Args:
        runtime: The runtime.

    Returns:
        Its card.
    """

    async def look() -> dict[str, object]:
        state = json.loads((await call(reopened(runtime), "GET /api/state")).body)
        card: dict[str, object] = state["events"][0]
        return card

    return asyncio.run(look())


def test_a_page_choice_after_a_workbook_edit_wins(locations: Locations) -> None:
    """The page saw the workbook's name, then chose another: the page's is newer."""
    runtime, workbook = classified(locations)
    name_first_event(workbook, LATER)
    card = _name_here(reopened(runtime))
    assert card["workbook"] == {
        "text": LATER,
        "name": LATER,
        "category": "",
        "stay": False,
    }
    inputs = load_inputs(runtime, find_workbook(runtime, None))
    assert (inputs.page.applied, inputs.page.replaced, inputs.edit_count) == (1, 1, 1)
    sort(runtime)
    assert (locations.data_dir / "c/2016" / EVENT_NAME / "IMG_0000.jpg").is_file()


def test_a_workbook_edit_after_a_page_choice_is_a_conflict(
    locations: Locations,
) -> None:
    """Refused by sort, shown in red by the page, settled by taking the choice back."""
    runtime, workbook = classified(locations)
    _name_here(reopened(runtime))
    name_first_event(workbook, LATER)
    with pytest.raises(WorkbookError) as refused:
        sort(runtime)
    assert f"page '{EVENT_NAME}', workbook '{LATER}'" in refused.value.message
    assert "review-sort" in (refused.value.tip or "")
    assert (locations.data_dir / PARTY / "IMG_0000.jpg").is_file()
    card = _card(runtime)
    assert card["conflict"]
    assert "shown in red" in output_of(runtime)
    app = reopened(runtime)

    async def take_back() -> None:
        await call(app, "POST /api/forget", {"event": card["id"]})

    asyncio.run(take_back())
    sort(runtime)
    assert (locations.data_dir / "c/2016" / LATER / "IMG_0000.jpg").is_file()


def test_the_same_choice_in_both_places_agrees(locations: Locations) -> None:
    """No conflict, nothing replaced: the workbook alone would say the same."""
    runtime, workbook = classified(locations)
    _name_here(reopened(runtime))
    name_first_event(workbook)
    inputs = load_inputs(runtime, find_workbook(runtime, None))
    assert (inputs.page.applied, inputs.page.agreed, inputs.edit_count) == (0, 1, 1)


def test_a_new_classify_carries_the_page_choices(locations: Locations) -> None:
    """Into the new workbook's yellow cells; a conflicting one is listed, not lost."""
    runtime, _workbook = classified(locations)
    _name_here(reopened(runtime))
    second = run_classify(runtime)
    assert "Choices of the review page carried over too: 1." in output_of(runtime)
    plan = plan_of(second)
    edits = read_edits(second.folder / "classify.xlsx", plan)
    assert list(edits.events.values()) == [EventEdit(EVENT_NAME, "")]
    name_first_event(second.folder / "classify.xlsx", LATER)
    _name_here(reopened(runtime), "Picnic")
    name_first_event(second.folder / "classify.xlsx", EVENT_NAME)
    third = run_classify(runtime)
    assert third.carried is not None
    lost = [(item.sheet, item.value, item.why) for item in third.carried.lost]
    assert lost == [(EditSheet.EVENTS, "Picnic", LostWhy.CONFLICT)]
    edits = read_edits(third.folder / "classify.xlsx", plan_of(third))
    assert list(edits.events.values()) == [EventEdit(EVENT_NAME, "")]
