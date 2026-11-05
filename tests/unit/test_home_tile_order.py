"""The tiles of *Where you are* hidden and moved: `[home] tiles` (0516)."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_state import home_state
from media_hygiene.cli.home_tile_order import arranged, read_tiles, save_tiles
from media_hygiene.review.home_more_api import (
    SAMPLES_PATH,
    TILES_PATH,
    HomeMore,
    more_response,
)
from media_hygiene.review.home_parts import HomeTile
from media_hygiene.review.home_paths import HOME_PATHS
from media_hygiene.review.http import Request
from media_hygiene.review.lan_paths import READ_PATHS
from media_hygiene.services.home import home_page
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}


def _tiles(*ids: str) -> tuple[HomeTile, ...]:
    """Tiles with these ids."""
    return tuple(
        HomeTile(id=name, label=name, value="", sub="", space="") for name in ids
    )


def _ids(tiles: tuple[HomeTile, ...]) -> list[str]:
    """Their ids."""
    return [tile.id for tile in tiles]


def test_the_order_is_applied_and_a_minus_hides() -> None:
    """Order = order, `-` = hidden, even a tile asking for action."""
    shown, hidden = arranged(_tiles("a", "b", "c"), ["c", "-b", "a"])
    assert _ids(shown) == ["c", "a"]
    assert _ids(hidden) == ["b"]


def test_an_unknown_id_is_ignored_and_a_new_tile_comes_last_shown() -> None:
    """A list written by an older version never hides a tile added since."""
    shown, hidden = arranged(_tiles("a", "b", "new"), ["gone", "-gone2", "b", "-a"])
    assert _ids(shown) == ["b", "new"]
    assert _ids(hidden) == ["a"]


def test_an_id_named_twice_counts_once() -> None:
    """A file edited by hand: the first word wins."""
    shown, hidden = arranged(_tiles("a"), ["a", "-a"])
    assert _ids(shown) == ["a"]
    assert not hidden


def test_empty_is_the_default() -> None:
    """Reset writes an empty list."""
    assert _ids(arranged(_tiles("a", "b"), [])[0]) == ["a", "b"]


def test_a_post_is_saved_read_back_and_comments_kept(tmp_path: Path) -> None:
    """The answer is what the file holds; a reset empties it."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("# mine\n[home]\n# keep me\n", "utf-8")
    more = HomeMore(config_file)

    def post(names: list[str]) -> dict[str, object]:
        body = json.dumps({"names": names}).encode()
        reply = asyncio.run(
            more_response(more, Request("POST", TILES_PATH, _JSON, body))
        )
        assert reply is not None
        assert reply.status is HTTPStatus.OK
        answer: dict[str, object] = json.loads(reply.body)
        return answer

    assert post(["copies", "-faces"]) == {"tiles": ["copies", "-faces"]}
    assert read_tiles(config_file) == ("copies", "-faces")
    assert "# keep me" in config_file.read_text("utf-8")
    assert post([]) == {"tiles": []}
    assert not read_tiles(config_file)


def test_a_get_saves_nothing_and_absent_routes_answer_nothing(tmp_path: Path) -> None:
    """Only a `POST` writes; other paths go on to `HomeApp`."""
    more = HomeMore(tmp_path / "config.toml")
    get = Request("GET", TILES_PATH, _JSON, b"")
    assert asyncio.run(more_response(more, get)) is None
    assert asyncio.run(more_response(HomeMore(), get)) is None
    other = Request("GET", SAMPLES_PATH, _JSON, b"")
    assert asyncio.run(more_response(more, other)) is None


def test_the_state_follows_the_file_and_every_tile_has_an_id(tmp_path: Path) -> None:
    """Read from disk at each state; ids are unique."""
    locations = make_locations(tmp_path)
    runtime = make_runtime(locations)
    every = _ids(home_state(runtime).tiles)
    assert len(set(every)) == len(every)
    assert all(every)
    save_tiles(locations.config_file, [every[-1], f"-{every[0]}"])
    state = home_state(runtime)
    assert state.tiles[0].id == every[-1]
    assert _ids(state.hidden_tiles) == [every[0]]


def test_the_routes_are_the_pc_s_and_the_page_can_edit() -> None:
    """Reach `HomeApp`; never a phone's. The page's edit mode is there."""
    assert {TILES_PATH, SAMPLES_PATH} <= HOME_PATHS
    assert not {TILES_PATH, SAMPLES_PATH} & READ_PATHS
    page = home_page().decode()
    assert "function tilesBlock()" in page
    assert TILES_PATH in page
