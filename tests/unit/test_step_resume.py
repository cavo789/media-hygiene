"""A long step followed from the page: reopened, it is shown again (0514)."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from media_hygiene.review.step_watch import WATCH, StepState, step_state
from media_hygiene.services.home import home_page
from media_hygiene.services.step_progress import PROGRESS_FILE

if TYPE_CHECKING:
    from pathlib import Path


def _state(folder: Path) -> dict[str, object]:
    """What `GET /api/step` answers the page that reopens."""
    reply = asyncio.run(step_state(folder))
    answer: dict[str, object] = json.loads(reply.body or b"{}")
    return answer


def test_a_running_step_is_found_again_with_its_stage(tmp_path: Path) -> None:
    """The tab closed: the step's id, state and stage are still there to follow."""
    (tmp_path / WATCH.running).write_text(json.dumps({"id": "abc"}), "utf-8")
    progress = {"title": "Exact copies", "done": 5, "total": 10, "current": "a.jpg"}
    (tmp_path / PROGRESS_FILE).write_text(json.dumps(progress), "utf-8")
    said = _state(tmp_path)
    assert said["state"] == StepState.RUNNING
    assert said["id"] == "abc"
    assert said["progress"] == progress


def test_nothing_running_nothing_to_resume(tmp_path: Path) -> None:
    """No step file: the page opens no follow dialog."""
    assert _state(tmp_path)["state"] == StepState.IDLE


def test_the_page_resumes_and_shows_the_pace() -> None:
    """The home page follows a running step on load, with its stage, bar and rate."""
    page = home_page().decode()
    assert ".includes(step.state)) resumeStep(step.id);" in page
    assert "<progress max=" in page
    assert '"perSecond"' in page
