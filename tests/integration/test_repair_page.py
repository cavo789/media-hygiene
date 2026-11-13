"""0783: the damaged files' page lists, restores (read back) and undoes."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.cli.safety_more import damaged_line
from media_hygiene.review.repair_app import RepairApp
from media_hygiene.review.served_more import REPAIR_PAGE, SERVED_MORE
from media_hygiene.services.repair_pick import repair_state, restore_damaged
from media_hygiene.services.repair_serving import repair_page
from media_hygiene.services.reread import reread
from tests.support.damage import damage_library, flip
from tests.support.json_calls import answer, call

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_a_flipped_byte_is_listed_restored_read_back_and_undone(
    locations: Locations,
) -> None:
    """Acceptance: listed beside its copy, restored identical, Undo puts it back."""
    runtime, first, _twin = damage_library(locations)
    before = first.read_bytes()
    flip(first)
    damaged = first.read_bytes()
    reread(runtime)
    with ThreadPoolExecutor(1) as executor:
        app = RepairApp(runtime, repair_page(), executor)
        page = call(app, "GET /")
        assert page.status is HTTPStatus.OK
        assert b'id="restore"' in page.body
        tiles = answer(app, "GET /api/state")["tiles"]
        assert isinstance(tiles, list)
        assert [tile["name"] for tile in tiles] == ["IMG_0001.jpg"]
        tile = tiles[0]
        assert tile["good_copy"]
        assert not tile["in_quarantine"]
        assert call(app, "GET /" + tile["original"]).status is HTTPStatus.OK
        assert call(app, "POST /api/restore", {"keys": []}).status is (
            HTTPStatus.BAD_REQUEST
        )
        reply = answer(app, "POST /api/restore", {"keys": [tile["key"]]})
        assert reply["left"] == []
        assert len(reply["back"]) == 1  # type: ignore[arg-type]
        assert first.read_bytes() == before  # read back from the disk
        assert reply["state"] == {"tiles": []}
        undone = answer(app, "POST /api/undo-run", {"run": reply["run_id"]})
        assert undone["intact"] is True
    assert first.read_bytes() == damaged  # the damaged file is back, as it was


def test_a_copy_gone_meanwhile_is_refused_and_nothing_moves(
    locations: Locations,
) -> None:
    """Shown with its copy; the copy deleted; Restore: said, no run, file untouched."""
    runtime, first, twin = damage_library(locations)
    flip(first)
    reread(runtime)
    key = repair_state(runtime).tiles[0].key
    twin.unlink()
    damaged = first.read_bytes()
    done = restore_damaged(runtime, [key])
    assert done.run_id is None
    assert done.back == ()
    assert len(done.left) == 1
    assert "IMG_0001.jpg" in done.left[0]
    assert first.read_bytes() == damaged
    assert not any(locations.quarantine_dir.rglob("*.jpg"))


def test_the_card_offers_the_page_and_the_console_stays() -> None:
    """The card's line opens `repair` (the page); `clean --repair` is served here."""
    assert SERVED_MORE[("clean", "--repair")] == REPAIR_PAGE
    facts: object = type(
        "F", (), {"reread": type("R", (), {"read": 3, "damaged": 2})()}
    )()
    line = damaged_line(facts)  # type: ignore[arg-type]
    assert line.step == "repair"
    assert "mh clean --repair" in line.sub
