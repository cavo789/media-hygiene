"""0387: the Folder field of review-sort, its Destination line, its saved time."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.classify.page_decisions import read_page_decisions
from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.classify.workbook.edits import Edits, EventEdit, resolve
from media_hygiene.review.sort_destination import host_folder
from tests.support.sort_review import call, classified, first_event, reopened
from tests.support.sorting import EVENT_NAME, PARTY_SHOTS

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response

FOLDER = "Fêtes/Kermesse"


def plan_beside(workbook: Path) -> ClassifyPlan:
    """The plan of a classify run."""
    return ClassifyPlan.model_validate_json(
        workbook.with_name("plan.json").read_text("utf-8")
    )


def test_the_destination_is_where_sort_will_put_the_files(locations: Locations) -> None:
    """The line under the field: `resolve` on the plan and the value typed."""
    runtime, workbook = classified(locations)
    app = reopened(runtime)

    async def ask() -> tuple[str, list[Response]]:
        event, _rows = await first_event(app)
        bodies = [
            {"event": event, "folder": FOLDER},
            {"event": event, "folder": "", "name": EVENT_NAME},
            {"event": event, "folder": "../out"},
        ]
        return event, [await call(app, "POST /api/destination", b) for b in bodies]

    event, (typed, named, refused) = asyncio.run(ask())
    plan = plan_beside(workbook)
    decided = resolve(plan, Edits(events={event: EventEdit("", FOLDER)}))
    first = next(d for d in decided if d.row.event_id == event)
    assert first.folder is not None
    answer = json.loads(typed.body)
    assert answer["target"] == host_folder(first.row.root, first.folder)
    assert (answer["going"], answer["already"], answer["kept"]) == (PARTY_SHOTS, 0, 0)
    assert json.loads(named.body)["target"].endswith(EVENT_NAME)
    assert refused.status is HTTPStatus.UNPROCESSABLE_ENTITY
    assert json.loads(refused.body)["error"]
    assert not workbook.with_name("sort-decisions.json").exists()


def test_a_typed_name_over_the_proposed_folder_keeps_the_folder(
    locations: Locations,
) -> None:
    """With `{year}/{category}`, the name names the event, not its folder."""
    runtime, workbook = classified(locations)
    app = reopened(runtime)

    async def ask() -> Response:
        event, _rows = await first_event(app)
        state = json.loads((await call(app, "GET /api/state")).body)
        proposed = state["events"][0]["category"]
        body = {"event": event, "folder": proposed or FOLDER, "name": "Autre nom"}
        return await call(app, "POST /api/destination", body)

    answer = json.loads(asyncio.run(ask()).body)
    assert "Autre nom" not in answer["target"]
    assert answer["going"] == PARTY_SHOTS
    assert plan_beside(workbook).layout == "{year}/{category}"


def test_a_choice_shows_the_time_read_back_from_the_disk(locations: Locations) -> None:
    """The "validated here at 14:32" line: the time the decisions file holds."""
    runtime, workbook = classified(locations)
    app = reopened(runtime)

    async def choose() -> Response:
        event, _rows = await first_event(app)
        body = {"event": event, "category": FOLDER, "name": "Kermesse"}
        return await call(app, "POST /api/event", body)

    card = json.loads(asyncio.run(choose()).body)["card"]
    saved = read_page_decisions(
        workbook.with_name("sort-decisions.json"), plan_beside(workbook).plan_id
    )
    [event] = saved.events
    assert card["saved"]
    assert card["saved"] == event.saved
    assert card["prefix"] in {"", "2016/"}
