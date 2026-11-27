"""0810: the page of the photos to straighten — Apply now, refusals, turn and undo."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from http import HTTPStatus
from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.cli.people_straighten import suggest_straighten
from media_hygiene.faces.models import FACE_MODEL
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.turn_refusals import TurnRefusals
from media_hygiene.index.turn_rows import TurnGuess, TurnStore
from media_hygiene.paths.mounts import MountTable
from media_hygiene.review.ending import Ending
from media_hygiene.review.served_more import SERVED_MORE, STRAIGHTEN_PAGE
from media_hygiene.services.home_pages import HomeServer
from media_hygiene.services.straighten_serving import straighten_app
from media_hygiene.services.turn_pick import turn_jobs_now
from tests.support.damage import audit
from tests.support.json_calls import answer, call
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_ORIENTATION = 0x0112


def _proposed(locations: Locations) -> tuple[Runtime, list[Path]]:
    """Two camera JPEGs audited, a quarter turn proposed for each."""
    photos = locations.data_dir / "c" / "Photos"
    photos.mkdir(parents=True)
    paths = []
    for number, colour in enumerate(("red", "blue"), start=1):
        path = photos / f"IMG_000{number}.jpg"
        exif = Image.Exif()
        exif[_ORIENTATION] = 1
        Image.new("RGB", (40, 20), colour).save(path, "JPEG", exif=exif)
        paths.append(path)
    runtime = replace(
        make_runtime(locations), mounts=MountTable(frozenset({photos}), (), ())
    )
    audit(runtime)
    with FactsRepository.open(runtime.locations.index_file) as repository:
        store = TurnStore(repository.connection, FACE_MODEL)
        for path in paths:
            stat = path.stat()
            store.put(TurnGuess(path, stat.st_size, stat.st_mtime_ns, 90))
    return runtime, paths


def test_apply_shows_refusal_leaves_out_turn_is_undone(locations: Locations) -> None:
    """Acceptance: `id="applyNow"` served; refused: out of Apply; turned then undone."""
    runtime, (first, second) = _proposed(locations)
    before = second.read_bytes()
    with ThreadPoolExecutor(1) as executor:
        server = HomeServer(lambda: None, Ending(), executor)
        app = straighten_app(runtime, server)
        page = call(app, "GET /")
        assert page.status is HTTPStatus.OK
        assert b'id="applyNow"' in page.body
        assert b'id="turnPicked"' in page.body
        tiles = answer(app, "GET /api/state")["tiles"]
        assert isinstance(tiles, list)
        assert [(tile["name"], tile["turn"]) for tile in tiles] == [
            ("IMG_0001.jpg", 90),
            ("IMG_0002.jpg", 90),
        ]
        refused = answer(app, "POST /api/refuse", {"keys": [tiles[0]["key"]]})
        assert refused["done"] == 1  # read back from the index
        assert [job.path for job in turn_jobs_now(runtime)] == [second]
        turned = answer(app, "POST /api/restore", {"keys": [tiles[1]["key"]]})
        assert turned["done"] == 1
        assert turned["state"] == {"tiles": []}
        with Image.open(second) as image:
            assert image.getexif()[_ORIENTATION] == 6
        with Image.open(first) as image:
            assert image.getexif()[_ORIENTATION] == 1
        undone = answer(app, "POST /api/undo-run", {"run": turned["run_id"]})
        assert undone["intact"] is True
    assert second.read_bytes() == before


def test_no_apply_without_the_home_page_and_the_step_is_served_here(
    locations: Locations,
) -> None:
    """Opened alone: no Apply (`people --straighten` opens it in the home server)."""
    runtime, _paths = _proposed(locations)
    assert SERVED_MORE[("people", "--straighten")] == STRAIGHTEN_PAGE
    with ThreadPoolExecutor(1) as executor:
        app = straighten_app(runtime, HomeServer(None, Ending(), executor))
        assert b'id="applyNow"' not in call(app, "GET /").body


def test_people_ends_on_the_photos_to_straighten(locations: Locations) -> None:
    """`people` ends on the page with the turns' count; all refused: no line."""
    runtime, paths = _proposed(locations)
    assert suggest_straighten(runtime)
    runtime.output.finish()
    assert "2 photos lying on their side" in output_of(runtime)
    with FactsRepository.open(runtime.locations.index_file) as repository:
        TurnRefusals(repository.connection).refuse(paths)
    assert not suggest_straighten(runtime)
