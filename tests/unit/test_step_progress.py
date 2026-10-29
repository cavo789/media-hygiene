"""0361: a step that writes shares its progress with the home page, read-only for it."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, cast

from media_hygiene.review.step_watch import WATCH, StepState, step_state
from media_hygiene.scan.progress import NullProgress, Step
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from media_hygiene.services.step_progress import (
    PROGRESS_FILE,
    SharedProgress,
    read_progress,
    shared,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_shared_only_under_an_mh_that_keeps_the_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without `MEDIA_HYGIENE_LAUNCHER_STEPS=3` nothing is written in /reports."""
    inner = NullProgress()
    monkeypatch.delenv(LAUNCHER_STEPS_VARIABLE, raising=False)
    assert shared(inner, tmp_path) is inner
    (tmp_path / PROGRESS_FILE).write_text("{}", "utf-8")  # the last step's
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, WATCH.kept)
    assert isinstance(shared(inner, tmp_path), SharedProgress)
    assert not (tmp_path / PROGRESS_FILE).exists()


def test_progress_written_at_start_and_end_throttled_between(tmp_path: Path) -> None:
    """Start and stop always write; advances within half a second do not."""
    sink = SharedProgress(NullProgress(), tmp_path)
    sink.start(Step("Lighten"), 3)
    assert read_progress(tmp_path) == {
        "title": "Lighten",
        "done": 0,
        "total": 3,
        "current": "",
    }
    sink.current("a.mp4")
    sink.advance()
    assert read_progress(tmp_path) == {
        "title": "Lighten",
        "done": 0,
        "total": 3,
        "current": "",
    }
    sink.stop()
    assert read_progress(tmp_path) == {
        "title": "Lighten",
        "done": 1,
        "total": 3,
        "current": "a.mp4",
    }
    assert not (tmp_path / (PROGRESS_FILE + ".tmp")).exists()


def test_api_step_carries_the_progress_while_running(tmp_path: Path) -> None:
    """`GET /api/step` adds the progress to a step running; none when unreadable."""
    (tmp_path / WATCH.running).write_text(json.dumps({"id": "a1"}), "utf-8")
    reply = json.loads(asyncio.run(step_state(tmp_path)).body)
    assert "progress" not in cast("dict[str, object]", reply)
    (tmp_path / PROGRESS_FILE).write_text('{"done": 2, "total": 5}', "utf-8")
    reply = json.loads(asyncio.run(step_state(tmp_path)).body)
    assert reply["state"] == StepState.RUNNING
    assert reply["progress"] == {"done": 2, "total": 5}
    (tmp_path / PROGRESS_FILE).write_text("[1]", "utf-8")
    assert read_progress(tmp_path) is None
