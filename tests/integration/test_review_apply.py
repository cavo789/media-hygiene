"""0288: *Apply now* on the burst and near duplicates reviews, opened from home."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from media_hygiene.cli.home_state import home_state
from media_hygiene.review.home_views import STEP_EXIT_BASE
from media_hygiene.review.http import Request
from media_hygiene.services import review_serving, reviewing
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from tests.support.cli import run
from tests.support.places_map import JSON
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Callable

    from typer.testing import CliRunner, Result

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.ending import EndingDoor
    from media_hygiene.review.http import Response

PORT = 4243
type Call = tuple[str, object]  # `POST /api/decide`, its JSON body (None: a GET)
type Answers = tuple[list[Response], Result]
APPLY: Call = ("POST /api/apply", {})
PAGE: Call = ("GET /", None)


@dataclass(frozen=True, slots=True)
class Mode:
    """A review: its command, the module serving it, a choice its page saves."""

    arguments: tuple[str, ...]
    module: object
    choice: Call


@dataclass(frozen=True, slots=True)
class Visit:
    """A review opened, the calls its page sends, and whether from the home page."""

    mode: Mode
    calls: tuple[Call, ...]
    home: bool = True


BURSTS = Mode(
    ("review",),
    reviewing,
    ("POST /api/decide", {"choices": [{"series": 0, "discarded": [2]}]}),
)
NEAR = Mode(
    ("review", "--near"),
    review_serving,
    ("POST /api/near", {"choices": [{"group": 0, "action": "planned"}]}),
)
MODES = pytest.mark.parametrize("mode", [BURSTS, NEAR], ids=["bursts", "near"])


@pytest.fixture
def opened(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> Callable[[Visit], Answers]:
    """Opens a review, sends the calls as its page does, stops it: answers, result."""

    def visit(seen: Visit) -> Answers:
        answers: list[Response] = []

        async def serve(
            door: EndingDoor, _port: int, ready: Callable[[int], None]
        ) -> int:
            ready(PORT)
            for route, body in seen.calls:
                method, path = route.split()
                data = json.dumps(body).encode() if body is not None else b""
                headers = JSON if body is not None else {"host": "127.0.0.1"}
                answers.append(await door.handle(Request(method, path, headers, data)))
            if door.ending.asked is None:
                raise KeyboardInterrupt
            return door.ending.asked

        if seen.home:
            monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, "1")
        else:
            monkeypatch.delenv(LAUNCHER_STEPS_VARIABLE, raising=False)
        monkeypatch.setattr(seen.mode.module, "serve_until_ended", serve)
        return answers, run(cli, *seen.mode.arguments)

    return visit


@MODES
def test_apply_now_from_home_ends_on_the_apply_step(
    opened: Callable[[Visit], Answers], locations: Locations, mode: Mode
) -> None:
    """Opened from home with a choice: the button, the home step's exit code."""
    answers, result = opened(Visit(mode, (PAGE, mode.choice, APPLY)))
    page, decided, applied = answers[0], answers[1], answers[2]
    assert b'id="applyNow"' in page.body
    assert b"window.mhApplyNow" in page.body
    assert decided.status == 200, decided.body
    assert applied.status == 200, applied.body
    step = json.loads(applied.body)
    command = home_state(make_runtime(locations)).command_of(step["number"])
    assert command == step["command"]
    assert "--decisions" in step["command"]
    assert result.exit_code == STEP_EXIT_BASE + step["number"], result.output
    said = " ".join(result.output.split())
    assert f"Apply now, chosen on the page: {command}" in said
    assert "What next" not in result.output  # mh runs the step: no line to type


@MODES
def test_opened_directly_no_button_and_the_next_line_stays(
    opened: Callable[[Visit], Answers], mode: Mode
) -> None:
    """`mh review` alone: no button, refused; the 👉 next step line stays."""
    answers, result = opened(Visit(mode, (PAGE, mode.choice, APPLY), home=False))
    assert b'id="applyNow"' not in answers[0].body
    assert answers[2].status == 409
    assert result.exit_code == 0, result.output
    assert "--decisions" in result.output.split("What next")[-1]


@MODES
def test_nothing_chosen_refused_and_the_page_keeps_running(
    opened: Callable[[Visit], Answers], mode: Mode
) -> None:
    """Opened from home, nothing set aside: refused, the review ends on Ctrl+C."""
    answers, result = opened(Visit(mode, (APPLY,)))
    assert answers[0].status == 409
    assert json.loads(answers[0].body)["error"] == "Nothing set aside."
    assert result.exit_code == 0, result.output


def test_apply_answers_only_a_post_from_the_page(
    opened: Callable[[Visit], Answers],
) -> None:
    """A GET never ends the review."""
    answers, result = opened(Visit(BURSTS, (BURSTS.choice, ("GET /api/apply", None))))
    assert answers[1].status == 405
    assert result.exit_code == 0, result.output
