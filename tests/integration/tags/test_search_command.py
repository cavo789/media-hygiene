"""`media-hygiene search`: a table in the console, the page in the browser."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.review.http import Request
from media_hygiene.search.app import SearchApp
from media_hygiene.services import search_pages as search_service
from tests.support.cli import run
from tests.support.places_map import JSON, PORT

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.ending import EndingDoor
    from media_hygiene.review.http import Response


def fake_server(action: Callable[[SearchApp], Awaitable[None]]) -> object:
    """A server that says it is ready, lets `action` act, then gets Ctrl+C.

    When the page asked the server to end (*Apply now*), it ends with that code.
    """

    async def serve(door: EndingDoor, _port: int, ready: Callable[[int], None]) -> int:
        ready(PORT)
        assert isinstance(door.app, SearchApp)
        await action(door.app)
        if door.ending.asked is None:
            raise KeyboardInterrupt
        return door.ending.asked

    return serve


async def _call(app: SearchApp, route: str, body: object = None) -> Response:
    """Send one request as the page does; `route`: `POST /api/search`."""
    method, path = route.split()
    headers = JSON if body is not None else {"host": "127.0.0.1"}
    data = json.dumps(body).encode() if body is not None else b""
    return await app.handle(Request(method, path, headers, data))


def test_the_table_finds_by_folder_and_date_words(cli: CliRunner) -> None:
    """Words of the folders and dates, without a model; nothing found says how."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    found = run(cli, "search", "durbuy", "christmas")
    assert found.exit_code == 0, found.output
    assert "IMG_0.jpg" in found.output
    assert "3 files found." in found.output
    assert "search" in found.output.split("What next")[-1]
    limited = run(cli, "search", "--limit", "1", "durb*")
    assert "the first 1 are listed" in limited.output
    nothing = run(cli, "search", "zebra")
    assert nothing.exit_code == 0
    assert "Nothing found." in nothing.output


def test_the_table_finds_by_a_word_of_the_file_name(
    cli: CliRunner, locations: Locations
) -> None:
    """`Vidéos/Anniversaire Léa.jpg`: found by its name; `IMG_0.jpg` gives no word."""
    videos = locations.data_dir / "c" / "Photos" / "Vidéos"
    videos.mkdir()
    Image.new("RGB", (64, 48), (200, 30, 30)).save(videos / "Anniversaire Léa.jpg")
    assert run(cli, "audit").exit_code == 0
    assert run(cli, "tags", "--no-describe").exit_code == 0
    found = run(cli, "search", "anniversaire")
    assert "Anniversaire Léa.jpg" in found.output
    assert "1 file found." in found.output
    assert "Nothing found." in run(cli, "search", "name:img").output


def test_without_tags_or_without_an_index(cli: CliRunner, locations: Locations) -> None:
    """Before `tags`: said, with the command to run; no index: an error."""
    before = run(cli, "search", "durbuy")
    assert "No file has words yet" in before.output
    (locations.cache_dir / "index.sqlite").unlink()
    missing = run(cli, "search", "durbuy")
    assert missing.exit_code != 0
    assert "nothing to search yet" in " ".join(missing.output.split())


def test_the_page_searches_and_shows_the_pictures(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Search, filters, previews kept in the cache, the original; read-only."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    seen: dict[str, Response] = {}

    async def browse(app: SearchApp) -> None:
        asked = {"text": "durbuy", "year_from": 2022, "folder": "photos/2022"}
        seen["found"] = await _call(app, "POST /api/search", asked)
        hit = json.loads(seen["found"].body)["hits"][0]
        for name in ("thumb", "preview", "original"):
            seen[name] = await _call(app, f"GET {hit[name]}")
        seen["again"] = await _call(app, f"GET {hit['thumb']}")
        seen["page"] = await _call(app, "GET /")
        seen["unknown"] = await _call(app, "GET /thumb/999999.jpg")
        seen["bad"] = await _call(app, "POST /api/search", {"text": 3})

    monkeypatch.setattr(search_service, "serve_until_ended", fake_server(browse))
    result = run(cli, "search")
    assert result.exit_code == 0, result.output
    assert f"open http://127.0.0.1:{PORT}/ in your browser" in result.output
    assert "your photos were not changed" in result.output
    found = json.loads(seen["found"].body)
    assert found["total"] == 3
    hit = found["hits"][0]
    assert hit["folder"].endswith("Durbuy - ours")
    assert hit["tags"]["folder"] == ["Durbuy", "ours"]
    assert seen["thumb"].body.startswith(b"\xff\xd8")
    assert seen["again"].body == seen["thumb"].body
    assert any((locations.cache_dir / "previews").iterdir())
    assert seen["preview"].body.startswith(b"\xff\xd8")
    assert seen["original"].body.startswith(b"\xff\xd8")
    page = seen["page"]
    assert b"/api/search" in page.body
    assert "default-src 'none'" in page.policy
    assert seen["unknown"].status == 404
    assert seen["bad"].status == 400


def test_the_page_refuses_other_hosts_and_bodies(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Loopback `Host` only; a search is JSON from the page's own origin."""
    answers: list[int] = []

    async def attack(app: SearchApp) -> None:
        foreign = {"host": "evil.example", "content-type": "application/json"}
        requests = (
            Request("GET", "/", foreign),
            Request("POST", "/api/search", {"host": "127.0.0.1"}, b"{}"),
            Request("POST", "/api/search", JSON | {"origin": "http://evil"}, b"{}"),
            Request("PUT", "/api/search", JSON, b"{}"),
            Request("GET", "/nothing", JSON),
            Request("GET", "/original/x.jpg", JSON),
        )
        answers.extend([(await app.handle(request)).status for request in requests])

    monkeypatch.setattr(search_service, "serve_until_ended", fake_server(attack))
    assert run(cli, "search").exit_code == 0
    assert answers == [403, 415, 403, 405, 404, 404]


def test_status_counts_the_files_with_words(cli: CliRunner) -> None:
    """`status` says how many files have words, and that `search` finds them."""
    assert "Tags:" not in run(cli, "status").output
    assert run(cli, "tags", "--no-describe").exit_code == 0
    said = " ".join(run(cli, "status").output.split())
    assert "Tags: 19 files have words, 0 of them from the vision model" in said
