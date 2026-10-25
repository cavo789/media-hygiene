"""0355: the steps `mh` runs while the home server stays up, as the page sees them."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, cast

from media_hygiene.review.ending import Ending
from media_hygiene.review.home_fields import STEP_FILE_NAME
from media_hygiene.review.home_step import StepDoor, step_response
from media_hygiene.review.home_views import FIELDS_STEP, STEP_EXIT_BASE
from media_hygiene.review.http import Request
from media_hygiene.review.step_watch import WATCH, StepState, step_state

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.home_views import HomeState

_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}
_STEPS: Final = {3: "mh history", 4: "mh review", 5: "mh browse"}


class _Menu:
    """Stands for the home page's state: the command of each step number."""

    def command_of(self, number: int) -> str | None:
        """The command of step `number`."""
        return _STEPS.get(number)


def _door(tmp_path: Path) -> tuple[StepDoor, Ending]:
    """A door of an `mh` that keeps the server up, and its ending."""
    ending = Ending()
    door = StepDoor(
        lambda: cast("HomeState", _Menu()),
        ending,
        tmp_path,
        relays_steps=True,
        relays_fields=True,
        keeps=True,
    )
    return door, ending


def _post(door: StepDoor, body: dict[str, object]) -> tuple[int, dict[str, object]]:
    """Send a step chosen, as the page does."""
    request = Request("POST", "/api/step", _JSON, json.dumps(body).encode())
    reply = asyncio.run(step_response(door, request))
    return reply.status, json.loads(reply.body or b"{}")


def _state(tmp_path: Path) -> dict[str, object]:
    """What `GET /api/step` says."""
    reply = asyncio.run(step_state(tmp_path))
    return cast("dict[str, object]", json.loads(reply.body))


def test_a_console_step_is_handed_over_and_the_server_stays(tmp_path: Path) -> None:
    """Its words and id in the file `mh` watches; no end; the page can follow it."""
    door, ending = _door(tmp_path)
    status, body = _post(door, {"number": 3, "command": "mh history"})
    assert status == HTTPStatus.OK
    assert body["kept"] is True
    assert body["command"] == "mh history"
    assert ending.asked is None
    written = json.loads((tmp_path / WATCH.now).read_text("utf-8"))
    assert written == {"id": body["id"], "words": ["history"]}
    assert _state(tmp_path) == {
        "state": StepState.WAITING,
        "id": body["id"],
        "code": None,
    }


def test_a_second_step_waits_for_the_first(tmp_path: Path) -> None:
    """409 while a step waits or runs: one at a time in the window of mh."""
    door, ending = _door(tmp_path)
    assert _post(door, {"number": 3, "command": "mh history"})[0] == HTTPStatus.OK
    status, body = _post(door, {"number": 3, "command": "mh history"})
    assert status == HTTPStatus.CONFLICT
    assert "running in the window of mh" in str(body["error"])
    (tmp_path / WATCH.now).unlink()
    (tmp_path / WATCH.running).write_text('{"id": "x"}', "utf-8")
    assert _post(door, {"number": 4, "command": "mh review"})[0] == HTTPStatus.CONFLICT
    assert ending.asked is None


def test_a_page_step_still_ends_the_server(tmp_path: Path) -> None:
    """A page needs the port: its words in the one-shot file, the fields code."""
    door, ending = _door(tmp_path)
    status, _body = _post(door, {"number": 4, "command": "mh review"})
    assert status == HTTPStatus.OK
    assert ending.asked == STEP_EXIT_BASE + FIELDS_STEP
    written = json.loads((tmp_path / STEP_FILE_NAME).read_text("utf-8"))
    assert written == {"words": ["review"]}
    assert not (tmp_path / WATCH.now).exists()


def test_a_form_s_console_step_is_kept_too(tmp_path: Path) -> None:
    """An album's name typed in the form: the same channel, the server up."""
    door, ending = _door(tmp_path)
    fields = {"album": "Noël 2025"}
    status, body = _post(door, {"name": "album", "fields": fields})
    assert status == HTTPStatus.OK
    assert body["kept"] is True
    assert ending.asked is None
    written = json.loads((tmp_path / WATCH.now).read_text("utf-8"))
    assert written["words"] == ["album", "Noël 2025"]


def test_the_state_follows_what_mh_writes(tmp_path: Path) -> None:
    """Idle, running, then done with its exit code; a byte order mark is fine."""
    assert _state(tmp_path)["state"] == StepState.IDLE
    (tmp_path / WATCH.running).write_text('{"id": "a1"}', "utf-8")
    assert _state(tmp_path) == {"state": StepState.RUNNING, "id": "a1", "code": None}
    (tmp_path / WATCH.running).unlink()
    (tmp_path / WATCH.done).write_text('﻿{"id": "a1", "code": 2}', "utf-8")
    assert _state(tmp_path) == {"state": StepState.DONE, "id": "a1", "code": 2}


def test_a_page_served_here_is_a_plain_link(tmp_path: Path) -> None:
    """0356: browse and search, served by the home server: its path, nothing ends."""
    door, ending = _door(tmp_path)
    status, body = _post(door, {"number": 5, "command": "mh browse"})
    assert status == HTTPStatus.OK
    assert body == {"page": "/browse", "command": "mh browse"}
    assert ending.asked is None
    assert not (tmp_path / STEP_FILE_NAME).exists()
    assert not (tmp_path / WATCH.now).exists()
