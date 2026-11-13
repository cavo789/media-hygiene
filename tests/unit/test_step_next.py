"""The 👉 line of a step beside the home server, in `GET /api/step` (0762)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.review.step_files import WATCH, StepState, read_state
from media_hygiene.services.step_next import (
    NEXT_FILE,
    forget_next,
    note_next,
    read_next,
)
from media_hygiene.services.step_progress import RUNNING_FILE

if TYPE_CHECKING:
    from pathlib import Path


def test_a_step_beside_the_server_writes_its_line_plain(tmp_path: Path) -> None:
    """Running for the home page: the line is written without its markup."""
    (tmp_path / RUNNING_FILE).write_text('{"id": "a"}', "utf-8")
    note_next("[bold]mh clean[/] --tier exact", tmp_path)
    assert read_next(tmp_path) == "mh clean --tier exact"


def test_a_step_of_the_console_alone_writes_nothing(tmp_path: Path) -> None:
    """No step of the home page running: no file in the reports folder."""
    note_next("mh history", tmp_path)
    assert not (tmp_path / NEXT_FILE).exists()
    assert read_next(tmp_path) is None


def test_the_state_carries_the_line_once_done_only(tmp_path: Path) -> None:
    """Running: no line yet; done: `next`; forgotten: gone."""
    (tmp_path / RUNNING_FILE).write_text('{"id": "a"}', "utf-8")
    note_next("mh history", tmp_path)
    assert "next" not in read_state(tmp_path)
    (tmp_path / RUNNING_FILE).unlink()
    (tmp_path / WATCH.done).write_text(json.dumps({"id": "a", "code": 0}), "utf-8")
    state = read_state(tmp_path)
    assert state["state"] == StepState.DONE
    assert state["next"] == "mh history"
    forget_next(tmp_path)
    assert "next" not in read_state(tmp_path)


def test_a_damaged_file_says_nothing(tmp_path: Path) -> None:
    """Half written or not an object: no line, never an error."""
    (tmp_path / NEXT_FILE).write_text("[1]", "utf-8")
    assert read_next(tmp_path) is None
    (tmp_path / NEXT_FILE).write_text("{", "utf-8")
    assert read_next(tmp_path) is None
