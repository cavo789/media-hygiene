"""*Move to an event…* on the search page (0403), its filters (0347, 0348, 0407)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.services import search_pages as search_service
from tests.integration.tags.test_search_command import _call, fake_server
from tests.support.cli import run
from tests.support.search_page import serve_search

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.search.app import SearchApp

_DAY: Final = {"text": "", "day_from": "2022-12-25", "day_to": "2022-12-25"}


def test_the_photos_picked_are_shown_then_moved_without_a_rule(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Before classify: refused, said; after: a view, a name refused, then the move."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    found = serve_search(cli, monkeypatch, [("POST /api/search", _DAY)])[0]
    keys = [hit["key"] for hit in json.loads(found.body)["hits"]]
    assert keys
    early = serve_search(cli, monkeypatch, [("POST /api/move/view", {"keys": keys})])[0]
    assert early.status == 409
    assert "classify" in json.loads(early.body)["error"]
    assert run(cli, "classify").exit_code == 0
    config = locations.config_file.read_text(encoding="utf-8")
    answers = serve_search(
        cli,
        monkeypatch,
        [
            ("POST /api/move/view", {"keys": keys, "name": "Noël"}),
            ("POST /api/move", {"keys": keys, "name": " / "}),
            ("POST /api/move", {"keys": keys, "name": "Noël"}),
        ],
    )
    assert [answer.status for answer in answers] == [200, 409, 200]
    view = json.loads(answers[0].body)
    assert view["target"].endswith("2022\\2022-12\\Noël")
    assert sum(source["files"] for source in view["sources"]) == len(keys)
    assert "name" in json.loads(answers[1].body)["error"]  # no folder named
    done = json.loads(answers[2].body)
    assert done["moved"] + done["already"] + done["fixed"] + done["unknown"] == len(
        keys
    )
    moved = list(locations.data_dir.rglob("2022/2022-12/Noël/*"))
    assert len(moved) >= done["moved"] > 0
    assert locations.config_file.read_text(encoding="utf-8") == config  # no rule


def test_the_page_opens_on_a_folder_given(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0405: `search --folder` says the address with the folder; the page reads it."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    pages: list[str] = []

    async def page(app: SearchApp) -> None:
        pages.append((await _call(app, "GET /search")).body.decode())

    monkeypatch.setattr(search_service, "serve_until_ended", fake_server(page))
    result = run(cli, "search", "--folder", "Prints jan10")
    assert result.exit_code == 0, result.output
    assert "/?folder=Prints+jan10" in "".join(result.output.split())
    assert 'URLSearchParams(window.location.search).get("folder")' in pages[0]


def test_the_photos_not_sorted_yet_or_the_sorted_ones(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0407: both sides add up to every photo; a folder moved by hand changes side."""
    sorted_to = locations.data_dir / "c" / "2022" / "2022-12" / "Noël"
    moved = next(locations.data_dir.rglob("*.jpg"))
    sorted_to.mkdir(parents=True)
    moved.rename(sorted_to / moved.name)
    assert run(cli, "audit").exit_code == 0  # the index follows the hand move
    assert run(cli, "tags", "--no-describe").exit_code == 0
    every, left, done = (
        json.loads(answer.body)
        for answer in serve_search(
            cli,
            monkeypatch,
            [
                ("POST /api/search", {"text": "", "sorting": sorting})
                for sorting in ("all", "left", "sorted")
            ],
        )
    )
    assert left["total"] + done["total"] == every["total"]
    assert [hit["name"] for hit in done["hits"]] == [moved.name]
    # By folder too: another photo may share the name (rglob's order differs in the CI).
    assert all(not hit["folder"].endswith("Noël") for hit in left["hits"])
    assert [hit["folder"].endswith("Noël") for hit in done["hits"]] == [True]


def test_sort_by_and_show_are_applied_before_the_limit(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0347: *Show: photos*, *Sort by: size*: the largest photos first, server side."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    every, photos, small = (
        json.loads(answer.body)
        for answer in serve_search(
            cli,
            monkeypatch,
            [
                ("POST /api/search", {"text": ""}),
                ("POST /api/search", {"text": "", "kind": "photos", "order": "size"}),
                ("POST /api/search", {"text": "", "kind": "videos"}),
            ],
        )
    )
    assert photos["total"] + small["total"] <= every["total"]
    sizes = [hit["bytes"] for hit in photos["hits"]]
    assert sizes == sorted(sizes, reverse=True)
    assert all(
        not hit["name"].lower().endswith((".mp4", ".mov")) for hit in photos["hits"]
    )


def test_a_folder_of_the_tree_narrows_the_search_with_or_without_words(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0348: the tree's folder, empty words: every file of it and below, only them."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    calls: list[tuple[str, object]] = [
        ("GET /api/folders", None),
        ("POST /api/search", {"text": ""}),
        ("GET /search", None),
    ]
    answers = serve_search(cli, monkeypatch, calls)
    folders = json.loads(answers[0].body)["folders"]
    inner = next(
        node for node in folders if node["parent"] is not None and node["files"]
    )
    asked = {"text": "", "within": inner["inside"]}
    found = json.loads(
        serve_search(cli, monkeypatch, [("POST /api/search", asked)])[0].body
    )
    assert 0 < found["total"] < json.loads(answers[1].body)["total"]
    assert all(hit["folder"].startswith(inner["path"]) for hit in found["hits"])
    page = answers[2].body.decode()
    assert 'id="views"' not in page  # one page, no tabs (0408)
    assert 'id="tree"' in page


def test_the_heaviest_files_are_those_of_the_folder_view(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0408: no word, *Show: all*, *Sort by: size*: the order of `/api/heaviest`."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    answers = serve_search(
        cli,
        monkeypatch,
        [
            ("POST /api/heaviest", {"kind": "all", "order": "size", "limit": 10}),
            ("POST /api/search", {"text": "", "kind": "all", "order": "size"}),
        ],
    )
    heavy, found = answers[0], answers[1]
    first = [card["key"] for card in json.loads(heavy.body)["files"]]
    assert first
    assert [hit["key"] for hit in json.loads(found.body)["hits"]][: len(first)] == first
