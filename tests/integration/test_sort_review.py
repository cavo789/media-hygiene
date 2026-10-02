"""`review-sort`: the events of a proposal in the browser, each choice saved at once."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from media_hygiene.classify.page_decisions import read_page_decisions
from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.review.http import Request
from tests.support.sort_review import PAGE, call, classified, first_event, reopened
from tests.support.sorting import EVENT_NAME, PARTY, sort

if TYPE_CHECKING:
    from http import HTTPStatus

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response

PARTY_SHOTS = 6


def test_the_state_an_event_its_previews_and_a_choice(locations: Locations) -> None:
    """One event to decide; named here, it is saved with the workbook's value seen."""
    runtime, workbook = classified(locations)
    app = reopened(runtime)

    async def browse() -> dict[str, Response]:
        event, rows = await first_event(app)
        return {
            "state": await call(app, "GET /api/state"),
            "event": await call(app, f"GET /api/event/{event}"),
            "thumb": await call(app, f"GET /thumb/{rows[0]}.jpg"),
            "large": await call(app, f"GET /preview/{rows[0]}.jpg"),
            "chosen": await call(
                app, "POST /api/event", {"event": event, "name": EVENT_NAME}
            ),
        }

    seen = asyncio.run(browse())
    state = json.loads(seen["state"].body)
    [card] = state["events"]
    assert state["workbook"] == str(workbook)
    assert card["undecided"] == card["files"] == PARTY_SHOTS
    assert card["page"] is None
    assert not card["workbook"]["text"]
    assert len(json.loads(seen["event"].body)["photos"]) == PARTY_SHOTS
    assert seen["thumb"].body.startswith(b"\xff\xd8")
    assert seen["thumb"].cacheable
    assert len(seen["large"].body) > len(seen["thumb"].body)
    assert json.loads(seen["chosen"].body)["card"]["page"]["name"] == EVENT_NAME
    plan = ClassifyPlan.model_validate_json(
        workbook.with_name("plan.json").read_text("utf-8")
    )
    saved = read_page_decisions(workbook.with_name("sort-decisions.json"), plan.plan_id)
    [event] = saved.events
    assert (event.value.name, event.base.empty) == (EVENT_NAME, True)
    result = sort(runtime)
    assert (locations.data_dir / "c/2016" / EVENT_NAME / "IMG_0000.jpg").is_file()
    assert result.manifest.intact


def test_photos_sent_elsewhere_or_left_in_place(locations: Locations) -> None:
    """One photo to another category, one left where it is; both applied by sort."""
    runtime, _workbook = classified(locations)
    app = reopened(runtime)

    async def choose() -> Response:
        event, rows = await first_event(app)
        body = {"event": event, "rows": rows[:1], "category": "Best of"}
        await call(app, "POST /api/files", body)
        stay = {"event": event, "rows": rows[1:2], "stay": True}
        return await call(app, "POST /api/files", stay)

    photos = json.loads(asyncio.run(choose()).body)["photos"]
    chosen = [photo["page"] for photo in photos[:2]]
    assert chosen == ["2016/Best of", "(stay where it is)"]
    sort(runtime)
    data = locations.data_dir
    assert (data / "c/2016/Best of/IMG_0000.jpg").is_file()
    assert (data / PARTY / "IMG_0001.jpg").is_file()


def test_refusals_never_save_anything(locations: Locations) -> None:
    """Unknown event or photo, a name Windows refuses, nothing chosen, bad requests."""
    runtime, workbook = classified(locations)
    app = reopened(runtime)

    async def refused() -> list[HTTPStatus]:
        event, rows = await first_event(app)
        bodies = [
            ("POST /api/event", {"event": "nope", "name": "X"}),
            ("POST /api/event", {"event": event}),
            ("POST /api/event", {"event": event, "name": "a/../b"}),
            ("POST /api/files", {"event": event, "rows": ["nope"], "category": "X"}),
            ("POST /api/files", {"event": event, "rows": rows[:1]}),
            ("POST /api/files", {"event": event, "rows": rows[:1], "category": ".."}),
            ("POST /api/forget", {"event": event, "extra": 1}),
        ]
        statuses = [(await call(app, *request)).status for request in bodies]
        assert (await call(app, "GET /")).body == PAGE
        others = [
            await call(app, "GET /api/event/nope"),
            await call(app, "GET /thumb/nope.jpg"),
            await call(app, f"GET /thumb/{rows[0]}.png"),
            await call(app, "PUT /api/event"),
            await app.handle(Request("POST", "/api/event", {"host": "127.0.0.1"})),
            await app.handle(Request("GET", "/", {"host": "evil.example"})),
        ]
        return statuses + [response.status for response in others]

    assert asyncio.run(refused()) == [422] * 7 + [404, 404, 404, 405, 415, 403]
    assert not workbook.with_name("sort-decisions.json").exists()
