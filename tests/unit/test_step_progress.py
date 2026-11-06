"""0361: a step that writes shares its progress with the home page, read-only for it."""

from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING, cast

from media_hygiene.review.step_watch import WATCH, StepState, step_state
from media_hygiene.scan.progress import NullProgress, Step
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from media_hygiene.services.step_progress import (
    LOST_AFTER_SECONDS,
    PROGRESS_FILE,
    RUNNING_FILE,
    SharedProgress,
    forget_progress,
    read_progress,
    shared,
    step_lost,
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


def _follow(folder: Path) -> dict[str, object]:
    """What the page reads."""
    answer: dict[str, object] = json.loads(
        asyncio.run(step_state(folder)).body or b"{}"
    )
    return answer


def test_the_step_mh_runs_beside_the_server_writes_without_the_variable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the server has the variable: `mh`'s file tells the step (0632)."""
    assert WATCH.running == RUNNING_FILE
    monkeypatch.delenv(LAUNCHER_STEPS_VARIABLE, raising=False)
    (tmp_path / WATCH.running).write_text('{"id": "a"}', "utf-8")
    assert isinstance(shared(NullProgress(), tmp_path), SharedProgress)


def test_a_step_advancing_then_ending_as_the_page_reads_it(tmp_path: Path) -> None:
    """The figure comes from the file; the end from `mh`'s, with its code (0632)."""
    (tmp_path / WATCH.running).write_text('{"id": "a"}', "utf-8")
    sink = SharedProgress(NullProgress(), tmp_path)
    sink.start(Step("Lighten"), 12)
    for _ in range(3):
        sink.advance()
    sink.current("c.mp4")
    sink.stop()
    said = _follow(tmp_path)
    assert said["state"] == StepState.RUNNING
    assert "lost" not in said
    assert said["progress"] == {
        "title": "Lighten",
        "done": 3,
        "total": 12,
        "current": "c.mp4",
    }
    (tmp_path / WATCH.running).unlink()
    (tmp_path / WATCH.done).write_text('{"id": "a", "code": 1}', "utf-8")
    ended = _follow(tmp_path)
    assert (ended["state"], ended["code"]) == (StepState.DONE, 1)  # a failure, said


def test_a_closed_window_is_said_and_a_slow_end_heals(tmp_path: Path) -> None:
    """No pulse for too long: lost; `mh`'s last word still replaces it (0632)."""
    (tmp_path / WATCH.running).write_text('{"id": "a"}', "utf-8")
    old = time.time() - LOST_AFTER_SECONDS - 1
    said = {"done": 3, "total": 12, "current": "", "at": old}
    (tmp_path / PROGRESS_FILE).write_text(json.dumps(said), "utf-8")
    assert step_lost(tmp_path)
    lost = _follow(tmp_path)
    assert lost["lost"] is True
    assert lost["progress"] == {"done": 3, "total": 12, "current": ""}
    (tmp_path / WATCH.running).unlink()
    (tmp_path / WATCH.done).write_text('{"id": "a", "code": 0}', "utf-8")
    assert "lost" not in _follow(tmp_path)


def test_the_pulse_goes_on_while_one_long_video_encodes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing advances, the time is written all the same; the end stops it (0632)."""
    monkeypatch.setattr("media_hygiene.services.step_progress.BEAT_SECONDS", 0.01)
    sink = SharedProgress(NullProgress(), tmp_path)
    sink.start(Step("Lighten"), 1)
    file = tmp_path / PROGRESS_FILE
    first = json.loads(file.read_text("utf-8"))["at"]
    deadline = time.monotonic() + 5
    while json.loads(file.read_text("utf-8"))["at"] == first:
        assert time.monotonic() < deadline
    sink.stop()
    assert not step_lost(tmp_path)


def test_an_old_progress_does_not_condemn_the_next_step(tmp_path: Path) -> None:
    """Without a file, or a file without a pulse, nothing is judged (0632)."""
    assert not step_lost(tmp_path)
    (tmp_path / PROGRESS_FILE).write_text('{"done": 1}', "utf-8")
    assert not step_lost(tmp_path)
    forget_progress(tmp_path)
    assert not (tmp_path / PROGRESS_FILE).exists()
