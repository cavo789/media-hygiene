"""0822: the plan-based choices left the *🗂 Events* view: 404, never a traceback."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus

from media_hygiene.review.http import Request
from media_hygiene.search.events_choose import events_get, sort_post

_JSON = {"host": "127.0.0.1", "content-type": "application/json"}


def test_the_plan_routes_are_gone_and_a_page_without_the_view_answers_404() -> None:
    """`/api/sort/event` and `/api/events` are no route of the view any more."""
    request = Request("POST", "/api/sort/event", _JSON, json.dumps({}).encode())
    assert asyncio.run(sort_post(None, request)).status == HTTPStatus.NOT_FOUND
    assert events_get(None, "/api/events") is None
