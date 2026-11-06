"""`undo --pick` (0525): a few quarantined photos put back, the rest still undoable."""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from typer.testing import CliRunner

from media_hygiene.actions.journal import done_states, journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.cli.app import build_app
from media_hygiene.review.http import Request
from media_hygiene.review.quarantine_app import QuarantineApp
from media_hygiene.review.served_more import DISK_PURGE_PATH
from media_hygiene.review.step_watch import WATCH
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.disk_here import DiskHere
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from media_hygiene.services.quarantine_pick import (
    quarantine_state,
    quarantined,
    restore_picked,
)
from media_hygiene.services.quarantine_serving import quarantine_page
from media_hygiene.services.undo import undo_run
from tests.support.cleaning import clean
from tests.support.cli import point_mounts
from tests.support.demo import build_demo
from tests.support.json_calls import answer, call
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response
    from media_hygiene.services.runtime import Runtime


def test_a_photo_restored_is_back_and_undo_brings_the_rest(
    locations: Locations,
) -> None:
    """One file back, read from the disk; the others stay; `undo` still works."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    known = quarantined(runtime)
    assert len(known) >= 2
    key, entry = next(iter(known.items()))
    restored = restore_picked(runtime, [key])
    assert Path(entry.path).is_file()  # read back from the disk
    assert restored.back == (entry.host_path,)
    assert not Path(str(entry.quarantine)).exists()
    left = {tile.key for tile in restored.state.tiles}
    assert key not in left
    assert left == set(known) - {key}
    undone = done_states(
        read_journal(journal_file(locations.journal_dir, run_id)), Phase.UNDO
    )
    files_undone = [
        each.seq for each in undone if each.action is not ActionKind.REMOVE_FOLDER
    ]
    assert files_undone == [entry.seq]  # journaled, that file only (its folder with it)
    outcome = undo_run(runtime, run_id, NullProgress())
    assert not outcome.failed
    assert not outcome.skipped  # the file restored is not taken back twice
    assert outcome.done >= len(known) - 1
    assert all(Path(each.path).is_file() for each in known.values())
    assert quarantine_state(runtime).tiles == ()


def test_the_page_lists_and_restores_through_its_routes(locations: Locations) -> None:
    """`GET /api/state`, a preview, then `POST /api/restore`; a bad body is refused."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    clean(runtime)
    with ThreadPoolExecutor(1) as executor:
        app = QuarantineApp(runtime, quarantine_page(), executor)
        assert call(app, "GET /").status is HTTPStatus.OK
        tiles = answer(app, "GET /api/state")["tiles"]
        assert isinstance(tiles, list)
        first = tiles[0]
        assert call(app, "GET /" + first["original"]).status is HTTPStatus.OK
        assert call(app, "POST /api/restore", {"keys": []}).status is (
            HTTPStatus.BAD_REQUEST
        )
        reply = answer(app, "POST /api/restore", {"keys": [first["key"]]})
        assert reply["back"]
        state = reply["state"]
        assert isinstance(state, dict)
        assert len(state["tiles"]) == len(tiles) - 1
        assert call(app, "GET /original/unknown~1.jpg").status is HTTPStatus.NOT_FOUND


def test_an_empty_quarantine_lists_nothing(locations: Locations) -> None:
    """No run yet: no tile, and a restore of an unknown key changes nothing."""
    runtime = make_runtime(locations)
    assert quarantine_state(runtime).tiles == ()
    assert restore_picked(runtime, ["nothing~1"]).back == ()


def test_undo_pick_serves_the_page_once_a_run_exists(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`undo --pick` serves the page on the port given; without a run it refuses."""
    point_mounts(locations, monkeypatch)
    locations.data_dir.mkdir(parents=True, exist_ok=True)
    ports: list[int] = []

    def served(_runtime: object, port: int) -> int:
        ports.append(port)
        return 0

    monkeypatch.setattr(
        "media_hygiene.services.quarantine_serving.serve_quarantine", served
    )
    refused = CliRunner().invoke(build_app(), ["undo", "--pick"])
    assert refused.exit_code != 0
    assert not ports
    build_demo(locations.data_dir)
    clean(make_runtime(locations))
    result = CliRunner().invoke(build_app(), ["undo", "--pick", "--port", "9123"])
    assert result.exit_code == 0, result.output
    assert ports == [9123]


def _purge_here(locations: Locations) -> tuple[DiskHere, Runtime]:
    """The disk space page on a real quarantine."""
    runtime = make_runtime(locations)
    fresh: Any = SimpleNamespace(runtime=lambda: runtime)
    return DiskHere(fresh), runtime


def _purge_post(here: DiskHere, body: dict[str, object]) -> Response:
    """Send `POST …/api/purge`."""
    headers = {"host": "127.0.0.1", "content-type": "application/json"}
    request = Request("POST", DISK_PURGE_PATH, headers, json.dumps(body).encode())
    return asyncio.run(here.handle(request))


def test_no_purge_without_the_files_shown_first(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No count, or another count than the run's tiles: refused, no step written."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, WATCH.kept)
    build_demo(locations.data_dir)
    here, runtime = _purge_here(locations)
    run_id = clean(runtime)
    shown = sum(tile.run == run_id for tile in quarantine_state(runtime).tiles)
    assert _purge_post(here, {"run_id": run_id}).status == HTTPStatus.BAD_REQUEST
    late = {"run_id": run_id, "files": shown + 1}
    assert _purge_post(here, late).status == HTTPStatus.CONFLICT
    unknown = {"run_id": "nope", "files": 1}
    assert _purge_post(here, unknown).status == HTTPStatus.CONFLICT
    assert not (locations.reports_dir / WATCH.now).exists()


def test_a_purge_is_handed_to_mh_then_read_back_from_the_disk(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The step with `--yes`, the server up; the state tells the room freed, stated."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, WATCH.kept)
    build_demo(locations.data_dir)
    here, runtime = _purge_here(locations)
    run_id = clean(runtime)
    shown = sum(tile.run == run_id for tile in quarantine_state(runtime).tiles)
    answer = _purge_post(here, {"run_id": run_id, "files": shown})
    assert answer.status == HTTPStatus.OK
    written = json.loads((locations.reports_dir / WATCH.now).read_text("utf-8"))
    assert written["words"] == ["purge", run_id, "--yes"]
    state_request = Request("GET", "/disk-space/api/state", {"host": "127.0.0.1"})
    before = json.loads(asyncio.run(here.handle(state_request)).body)["purged"]
    assert before["gone"] is False

    runner = CliRunner()
    point_mounts(locations, monkeypatch)
    done = runner.invoke(build_app(), ["purge", run_id, "--yes"])
    assert done.exit_code == 0, done.output
    after = json.loads(asyncio.run(here.handle(state_request)).body)["purged"]
    assert after["gone"] is True
    assert after["freed"] == after["stated"]


def test_a_purge_refused_when_mh_does_not_keep_the_server(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A server `mh` does not watch: nothing written, the sentence said."""
    monkeypatch.delenv(LAUNCHER_STEPS_VARIABLE, raising=False)
    here, _runtime = _purge_here(locations)
    answer = _purge_post(here, {"run_id": "x", "files": 1})
    assert answer.status == HTTPStatus.CONFLICT
