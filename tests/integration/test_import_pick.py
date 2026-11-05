"""`import --pick` (0590): the new files seen, some left out, the others copied."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, cast

from media_hygiene.review.import_pick_app import ImportPickApp
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.import_pick import ImportDesk
from media_hygiene.services.import_pick_serving import import_page
from media_hygiene.services.import_pick_tiles import LEFT_OUT_FILE
from media_hygiene.services.import_run import ImportService
from tests.support.json_calls import answer, call
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime


def _files(locations: Locations) -> tuple[Runtime, Path]:
    """A library with one photo, a backup with three new files."""
    library = locations.data_dir / "c" / "Photos"
    backup = locations.data_dir / "e" / "DCIM"
    library.mkdir(parents=True)
    backup.mkdir(parents=True)
    (library / "kept.jpg").write_bytes(b"kept" * 100)
    for name in ("a", "b", "c"):
        (backup / f"{name}.mov").write_bytes(name.encode() * 400)
    layer: dict[str, Any] = {"folders": {"backups": [str(backup)]}}
    runtime = make_runtime(locations).with_overrides(layer)
    return runtime, backup


def _wait_copied(app: ImportPickApp) -> dict[str, Any]:
    """The state once the copy has ended."""
    for _try in range(200):
        state = cast("dict[str, Any]", answer(app, "GET /api/state"))
        if not state["copying"]:
            return state
        time.sleep(0.02)
    raise AssertionError


def test_a_file_unpicked_is_not_copied_and_the_folder_is_untouched(
    locations: Locations,
) -> None:
    """Tiles of the new files; one left out, read back; a wrong count refused."""
    runtime, backup = _files(locations)
    before = {path.name: path.read_bytes() for path in backup.iterdir()}
    plan = ImportService(runtime, NullProgress()).prepare()
    assert len(plan.jobs) == 3
    with ThreadPoolExecutor(1) as executor:
        desk = ImportDesk(runtime, plan)
        app = ImportPickApp(runtime, desk, import_page(), executor)
        assert call(app, "GET /").status is HTTPStatus.OK
        tiles = answer(app, "GET /api/state")["tiles"]
        assert isinstance(tiles, list)
        assert {tile["name"] for tile in tiles} == {"a.mov", "b.mov", "c.mov"}
        assert call(app, "GET /" + tiles[0]["original"]).status is HTTPStatus.OK
        out = next(tile for tile in tiles if tile["name"] == "b.mov")
        left = answer(app, "POST /api/leave", {"keys": [out["key"]], "out": True})
        assert isinstance(left["tiles"], list)
        assert [t["name"] for t in left["tiles"] if t["left_out"]] == ["b.mov"]
        assert (runtime.locations.reports_dir / LEFT_OUT_FILE).is_file()
        refused = call(app, "POST /api/copy", {"count": 3})  # what no button states now
        assert refused.status is HTTPStatus.CONFLICT
        assert call(app, "POST /api/copy", {"count": 2}).status is HTTPStatus.OK
        state = _wait_copied(app)
    assert state["result"] is not None
    assert state["result"]["copied"] == 2
    assert state["result"]["failed"] == 0
    assert [tile["name"] for tile in state["tiles"]] == ["b.mov"]  # read from the disk
    copied = {job.source.name for job in plan.jobs if job.target.is_file()}
    assert copied == {"a.mov", "c.mov"}
    assert {path.name: path.read_bytes() for path in backup.iterdir()} == before


def test_a_file_brought_back_is_copied_and_a_moved_source_is_proposed_again(
    locations: Locations,
) -> None:
    """Choices by path: a key of no file is ignored, a file renamed is simply new."""
    runtime, backup = _files(locations)
    plan = ImportService(runtime, NullProgress()).prepare()
    desk = ImportDesk(runtime, plan)
    keys = [tile.key for tile in desk.state().tiles]
    desk.choose(keys[:1], out=True)
    assert len(desk.kept()) == 2
    desk.choose(keys[:1], out=False)
    desk.choose(["nothing"], out=True)
    assert len(desk.kept()) == 3
    desk.choose(keys, out=True)
    (backup / "a.mov").rename(backup / "z.mov")
    fresh = ImportDesk(runtime, ImportService(runtime, NullProgress()).prepare())
    assert [job.source.name for job in fresh.kept()] == ["z.mov"]
