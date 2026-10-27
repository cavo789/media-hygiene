"""0363: *Apply now* hands its step beside the home server, in words, or as a number."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import pytest

from media_hygiene.review.apply_api import ApplyDesk, ApplyOffer, ApplyStep
from media_hygiene.review.apply_relay import ApplyRelay, home_relay
from media_hygiene.review.ending import Ending
from media_hygiene.review.home_fields import STEP_FILE_NAME
from media_hygiene.review.home_views import FIELDS_STEP, STEP_EXIT_BASE
from media_hygiene.review.step_watch import STEP_PATH, WATCH
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE

if TYPE_CHECKING:
    from pathlib import Path

_STEP = ApplyStep(7, "mh clean --decisions")
_WORDS = ["clean", "--decisions"]


def _apply(relay: ApplyRelay | None) -> tuple[dict[str, object], Ending]:
    """Click *Apply now* with something set aside: the answer and the server's end."""
    ending = Ending()
    desk = ApplyDesk(ApplyOffer(lambda: _STEP, lambda: True), ending, relay)
    answer = asyncio.run(desk.answer())
    assert answer.status == 200, answer.body
    said: dict[str, object] = json.loads(answer.body)
    return said, ending


def test_kept_up_the_step_runs_beside_the_home_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Browse on the home server, `mh` keeping it up: `.mh-step-now.json`, no end."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, WATCH.kept)
    said, ending = _apply(home_relay(tmp_path))
    assert ending.asked is None  # the home server stays up
    assert said["kept"] is True
    assert said["follow"] == STEP_PATH
    assert said["command"] == _STEP.command
    written = json.loads((tmp_path / WATCH.now).read_text("utf-8"))
    assert written == {"id": said["id"], "words": _WORDS}
    assert not (tmp_path / STEP_FILE_NAME).exists()


@pytest.mark.parametrize("mode", ["2", WATCH.kept])
def test_own_server_ends_with_the_words_in_the_one_shot_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    """A review of its own, or an `mh` reading the file: the words, the fields code."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, mode)
    said, ending = _apply(ApplyRelay(tmp_path))
    assert ending.asked == STEP_EXIT_BASE + FIELDS_STEP
    assert said == {"number": _STEP.number, "command": _STEP.command}
    written = json.loads((tmp_path / STEP_FILE_NAME).read_text("utf-8"))
    assert written == {"words": _WORDS}
    assert not (tmp_path / WATCH.now).exists()


@pytest.mark.parametrize("beside", [True, False])
def test_an_older_mh_gets_the_number(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, beside: bool
) -> None:
    """`MEDIA_HYGIENE_LAUNCHER_STEPS=1`: the step's number, nothing written."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, "1")
    _said, ending = _apply(ApplyRelay(tmp_path, beside=beside))
    assert ending.asked == STEP_EXIT_BASE + _STEP.number
    assert not list(tmp_path.iterdir())


def test_no_relay_or_an_unwritable_folder_gets_the_number(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No reports folder given, or one that cannot be written: the number, as before."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, "2")
    assert _apply(None)[1].asked == STEP_EXIT_BASE + _STEP.number
    missing = ApplyRelay(tmp_path / "gone")
    assert _apply(missing)[1].asked == STEP_EXIT_BASE + _STEP.number
