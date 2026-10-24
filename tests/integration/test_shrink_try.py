"""`shrink --try`: drafts compared in the page, lightened from it, always gone (0307).

The page is driven through its app (the routes the browser calls), the server stood
in for: the drafts are real `ffmpeg` encodings of synthetic clips.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.actions import shrink_draft
from media_hygiene.cli import shrink_flow
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request
from media_hygiene.review.shrink_app import LIGHTEN_CODE, ShrinkDesk, ShrinkTryApp
from media_hygiene.services.runtime import Runtime
from media_hygiene.services.shrink_page import try_page
from media_hygiene.shrink import draft_bench
from media_hygiene.shrink.draft_bench import DraftState
from media_hygiene.shrink.drafts import drafts_root
from media_hygiene.shrink.try_choices import CHOICES_FILE, read_choices
from tests.support.cli import run
from tests.support.shrink_clips import CAMERA, NEEDS_X264, audited

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response
    from media_hygiene.services.shrink_try import Trial

pytestmark = NEEDS_X264
_LOCAL: Final = {"host": "127.0.0.1:8088"}
_JSON: Final = {**_LOCAL, "content-type": "application/json"}
_WAIT_SECONDS: Final = 60.0

type Scenario = Callable[[ShrinkTryApp, Trial], int]


@pytest.fixture
def cli(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """The camera's MJPEG clip (the one candidate), audited."""
    return audited(locations, monkeypatch)


def _ask(app: ShrinkTryApp, path: str, body: object = None) -> Response:
    """Send the page's request: a `GET`, or a `POST` with a JSON body."""
    if body is None:
        request = Request("GET", path, _LOCAL)
    else:
        request = Request("POST", path, _JSON, json.dumps(body).encode())
    return asyncio.run(app.handle(request))


def _settled(trial: Trial) -> None:
    """Wait until no draft waits nor encodes."""
    deadline = time.monotonic() + _WAIT_SECONDS
    busy = (DraftState.WAITING, DraftState.ENCODING)
    while any(draft.state in busy for draft in trial.bench.drafts()):
        assert time.monotonic() < deadline, "the drafts never ended"
        time.sleep(0.1)


def _page(monkeypatch: pytest.MonkeyPatch, scenario: Scenario) -> list[Trial]:
    """Stand in for the server: the scenario plays the user on the page's routes."""
    seen: list[Trial] = []

    def serve(runtime: Runtime, trial: Trial) -> int:
        seen.append(trial)
        _settled(trial)
        app = ShrinkTryApp(try_page(), ShrinkDesk(trial, runtime.mapper, Ending()))
        return scenario(app, trial)

    monkeypatch.setattr(shrink_flow, "serve_try", serve)
    return seen


def _left(locations: Locations) -> list[Path]:
    """What the drafts folder still holds."""
    root = drafts_root(locations.cache_dir)
    return sorted(root.rglob("*")) if root.is_dir() else []


def _close(app: ShrinkTryApp, trial: Trial) -> int:
    """Look at the draft, its frames and its state, then close the page."""
    (draft,) = trial.bench.drafts()
    assert draft.state is DraftState.READY, draft.reason
    assert (trial.bench.folder / "1.mp4").is_file()
    state = json.loads(_ask(app, "/api/state").body)
    (view,) = state["drafts"]
    assert view["gain"] > 0
    assert view["video"] == "/draft/1.mp4"
    assert len(view["frames"]) == 3
    assert state["file"] is None
    assert _ask(app, "/draft/1.mp4").status == 200
    assert _ask(app, view["frames"][0]["before"]).body.startswith(b"\xff\xd8")
    assert _ask(app, view["frames"][2]["after"]).body.startswith(b"\xff\xd8")
    assert _ask(app, "/draft/2.mp4").status == 404
    assert _ask(app, "/api/shrink/lighten", {}).status == 409  # nothing chosen
    foreign = Request("GET", "/api/state", {"host": "evil.example"})
    assert asyncio.run(app.handle(foreign)).status == 403
    return 0


def test_the_page_closed_removes_every_draft(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Shown, then closed: nothing changed, nothing left in /cache/shrink-try."""
    camera = locations.data_dir / CAMERA
    size = camera.stat().st_size
    seen = _page(monkeypatch, _close)
    result = run(cli, "shrink", "--try")
    assert result.exit_code == 0, result.output
    assert seen
    assert "Try stopped" in " ".join(result.output.split())
    assert camera.stat().st_size == size
    assert _left(locations) == []


def test_ctrl_c_removes_every_draft(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ctrl+C (`docker stop` too) in the middle of an encoding: killed, removed."""
    seen: list[Trial] = []

    def interrupted(_runtime: Runtime, trial: Trial) -> int:
        deadline = time.monotonic() + _WAIT_SECONDS
        while trial.bench.drafts()[0].state is DraftState.WAITING:
            assert time.monotonic() < deadline
            time.sleep(0.01)
        seen.append(trial)
        raise KeyboardInterrupt

    monkeypatch.setattr(shrink_flow, "serve_try", interrupted)
    result = run(cli, "shrink", "--try")
    assert result.exit_code != 0
    assert seen
    assert _left(locations) == []


def test_an_encoding_that_fails_is_said_and_removed(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A draft that lost something: said on the page, never kept."""
    monkeypatch.setattr(draft_bench, "flaw", lambda _files, _tools: "lost its sound")

    def failed(app: ShrinkTryApp, trial: Trial) -> int:
        (draft,) = trial.bench.drafts()
        assert draft.state is DraftState.FAILED
        assert not (trial.bench.folder / "1.mp4").exists()
        (view,) = json.loads(_ask(app, "/api/state").body)["drafts"]
        assert view["reason"] == "lost its sound"
        assert _ask(app, "/draft/1.mp4").status == 404
        return 0

    _page(monkeypatch, failed)
    assert run(cli, "shrink", "--try").exit_code == 0
    assert _left(locations) == []


def test_drafts_a_crash_left_are_removed_by_the_next_shrink(
    cli: CliRunner, locations: Locations
) -> None:
    """`docker kill`, the PC off: the next `shrink` empties the folder, in one line."""
    root = drafts_root(locations.cache_dir)
    left = root / "20261023-101010" / "1.mp4"
    left.parent.mkdir(parents=True)
    left.write_bytes(b"\0" * 3_000_000)
    (root / "try.lock").write_text("old 1\n")
    old = time.time() - 3600
    os.utime(root / "try.lock", (old, old))
    said = " ".join(run(cli, "shrink").output.split())
    assert "Previous drafts removed: 3 MB" in said
    assert _left(locations) == []


def test_a_second_try_at_once_is_refused_and_keeps_the_first_s_drafts(
    cli: CliRunner, locations: Locations
) -> None:
    """Another `shrink --try` holds the lock: refused; its drafts are not swept."""
    root = drafts_root(locations.cache_dir)
    draft = root / "20261023-101010" / "1.mp4"
    draft.parent.mkdir(parents=True)
    draft.write_bytes(b"draft")
    (root / "try.lock").write_text("other 1\n")
    result = run(cli, "shrink", "--try")
    assert result.exit_code == 1
    assert "Another 'shrink --try' is running" in " ".join(result.output.split())
    assert run(cli, "shrink").exit_code == 0
    assert draft.is_file()


def test_without_a_cache_mount_the_try_is_refused(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bare `docker run`: the line to add, never a folder inside the container."""
    original = Runtime.persistent

    def without_cache(self: Runtime, kind: MountKind) -> bool:
        return kind is not MountKind.CACHE and original(self, kind)

    monkeypatch.setattr(Runtime, "persistent", without_cache)
    result = run(cli, "shrink", "--try")
    assert result.exit_code == 1
    assert "in /cache only" in " ".join(result.output.split())
    assert _left(locations) == []


def _choose_then_lighten(app: ShrinkTryApp, trial: Trial) -> int:
    """Choose the draft, see the file read back from the disk, then lighten."""
    answer = json.loads(
        _ask(app, "/api/shrink/choose", {"drafts": [1], "chosen": True}).body
    )
    assert answer["file"]["chosen"] == [1]
    on_disk = read_choices(trial.choices)
    assert on_disk is not None
    assert [choice.draft for choice in on_disk.chosen] == [1]
    assert trial.choices.name == CHOICES_FILE
    lighten = _ask(app, "/api/shrink/lighten", {})
    assert json.loads(lighten.body) == {"count": 1}
    assert app.desk.ending.asked == LIGHTEN_CODE
    return LIGHTEN_CODE


def test_lightened_from_the_page_the_draft_is_reused(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Chosen on the page: the run moves the draft beside the original, no encoding."""

    def never(_command: tuple[str, ...], _duration: float) -> str | None:
        message = "encoded twice"
        raise AssertionError(message)

    monkeypatch.setattr(shrink_draft, "encode", never)
    _page(monkeypatch, _choose_then_lighten)
    result = run(cli, "shrink", "--try", "--yes")
    assert result.exit_code == 0, result.output
    assert "1 video lightened" in " ".join(result.output.split())
    camera = locations.data_dir / CAMERA
    assert not camera.exists()
    assert camera.with_suffix(".mp4").is_file()
    assert _left(locations) == []


def test_a_video_moved_since_the_page_is_skipped(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Renamed in the Explorer before the run: skipped with a line, nothing encoded."""
    camera = locations.data_dir / CAMERA
    moved = camera.with_name("moved.avi")

    def then_moved(app: ShrinkTryApp, trial: Trial) -> int:
        code = _choose_then_lighten(app, trial)
        camera.rename(moved)
        return code

    _page(monkeypatch, then_moved)
    result = run(cli, "shrink", "--try", "--yes")
    assert result.exit_code == 0, result.output
    said = " ".join(result.output.split())
    assert "changed since the page: skipped" in said
    assert "No video left to lighten" in said
    assert moved.is_file()
    assert not list(locations.journal_dir.glob("*.jsonl"))
    assert _left(locations) == []


def test_without_room_in_the_cache_the_drafts_stop(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Less than twice the estimate free: no draft, said on the page."""
    monkeypatch.setattr(draft_bench, "has_room", lambda _folder, _estimated: False)

    def full(app: ShrinkTryApp, trial: Trial) -> int:
        (draft,) = trial.bench.drafts()
        assert draft.state is DraftState.NO_ROOM
        state = json.loads(_ask(app, "/api/state").body)
        assert state["busy"] is False
        return 0

    _page(monkeypatch, full)
    assert run(cli, "shrink", "--try").exit_code == 0
    assert _left(locations) == []
