"""A slow answer of a page is logged with its laps; a quick one is not."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from media_hygiene.review import slow_log
from media_hygiene.review.slow_log import Laps, timed

if TYPE_CHECKING:
    import pytest


def test_slow_answer_logged_with_laps(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Over the threshold: one warning naming the request and each step."""
    monkeypatch.setattr(slow_log, "SLOW_SECONDS", 0.0)
    laps = Laps("naming Terry")
    laps.lap("read")
    laps.lap("write")
    with caplog.at_level(logging.WARNING):
        laps.said()
    assert "naming Terry" in caplog.text
    assert "read" in caplog.text
    assert "write" in caplog.text


def test_quick_answer_not_logged(caplog: pytest.LogCaptureFixture) -> None:
    """Under the threshold: nothing logged, the answer returned."""

    async def answer() -> int:
        return 7

    with caplog.at_level(logging.WARNING):
        assert asyncio.run(timed("GET /", answer())) == 7
    assert not caplog.text
