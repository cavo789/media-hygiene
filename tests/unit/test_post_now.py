"""The library's questions run beside the event loop, one at a time, in order."""

from __future__ import annotations

import asyncio
import threading
import time
from http import HTTPStatus
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.review.http import Response
from media_hygiene.search import post_now

if TYPE_CHECKING:
    import pytest

    from media_hygiene.review.http import Request
    from media_hygiene.search.coverage import CoverageKept
    from media_hygiene.search.place import SearchPlace

_SLOW = 0.2


def test_questions_leave_the_loop_free_and_keep_their_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two slow questions: answered in turn, while the loop serves a quick one."""
    seen: list[tuple[str, int]] = []

    def slow(_place: object, _coverage: object, request: SimpleNamespace) -> Response:
        seen.append((request.path, threading.get_ident()))
        time.sleep(_SLOW)
        seen.append((f"{request.path} done", threading.get_ident()))
        return Response(HTTPStatus.OK)

    monkeypatch.setattr(post_now, "answer_now", slow)
    place = cast("SearchPlace", SimpleNamespace(turn=asyncio.Lock()))
    coverage = cast("CoverageKept", None)

    async def run() -> float:
        loop_thread = threading.get_ident()
        first, second = (
            post_now.answer_in_turn(
                place, coverage, cast("Request", SimpleNamespace(path=path))
            )
            for path in ("/a", "/b")
        )
        started = time.perf_counter()
        both = asyncio.gather(first, second)
        await asyncio.sleep(0)  # a thumbnail, served meanwhile
        quick = time.perf_counter() - started
        await both
        assert all(ident != loop_thread for _, ident in seen)
        return quick

    assert asyncio.run(run()) < _SLOW
    assert [step for step, _ in seen] == ["/a", "/a done", "/b", "/b done"]
