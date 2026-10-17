"""`browse`: the tree of the folders, the files of one, set aside, then cleaned."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.http import Request
from media_hygiene.services import search_pages
from tests.integration.tags.test_search_command import _call, fake_server
from tests.support.cli import run
from tests.support.places_map import JSON

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response
    from media_hygiene.search.app import SearchApp

_BURST = "Durbuy - ours"


def _browse(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, object]]
) -> tuple[list[Response], str]:
    """Open the folder view, send the calls in order, stop it; answers, console."""
    answers: list[Response] = []

    async def browse(app: SearchApp) -> None:
        for route, body in calls:
            answers.append(await _call(app, route, body))

    monkeypatch.setattr(search_pages, "run_server", fake_server(browse))
    result = run(cli, "browse")
    assert result.exit_code == 0, result.output
    return answers, result.output


def _body(answer: Response) -> dict[str, list[dict[str, object]]]:
    """The JSON of an answer."""
    body: dict[str, list[dict[str, object]]] = json.loads(answer.body)
    return body


def test_the_tree_counts_what_the_index_holds(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every folder with its photos and size; the mounted one on top; no words."""
    answers, console = _browse(cli, monkeypatch, [("GET /api/folders", None)])
    assert "Your folders are ready, open http://127.0.0.1:" in console
    assert "No file has words yet" not in console
    folders = {str(node["name"]): node for node in _body(answers[0])["folders"]}
    with closing(sqlite3.connect(locations.cache_dir / "index.sqlite")) as index:
        (total,) = index.execute("SELECT COUNT(*) FROM files").fetchone()
    roots = [node for node in folders.values() if node["parent"] is None]
    assert [node["photos"] for node in roots] == [total]
    burst = folders[_BURST]
    assert (burst["photos"], burst["videos"], burst["files"]) == (3, 0, 3)
    assert str(burst["parent"]).endswith("2022")
    assert folders["2022"]["files"] == 0


def _dcim(cli: CliRunner, monkeypatch: pytest.MonkeyPatch) -> str:
    """The host path of the folder of the events, from the tree."""
    tree = _body(_browse(cli, monkeypatch, [("GET /api/folders", None)])[0][0])
    return str(next(n["path"] for n in tree["folders"] if n["name"] == "DCIM"))


def test_a_folder_by_name_and_by_date(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Its files only, sorted as asked."""
    folder = _dcim(cli, monkeypatch)
    answers = _browse(
        cli,
        monkeypatch,
        [
            ("POST /api/folder", {"folder": folder}),
            ("POST /api/folder", {"folder": folder, "order": "date"}),
        ],
    )[0]
    names = [str(file["name"]) for file in _body(answers[0])["files"]]
    assert names == sorted(names, key=str.casefold)
    assert all(name.startswith("IMG_") for name in names)
    days = [str(file["date"]) for file in _body(answers[1])["files"]]
    assert days == sorted(days)


def test_files_set_aside_are_read_back_then_cleaned(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two files picked: saved, marked, proposed; `clean` moves exactly them."""
    folder = _dcim(cli, monkeypatch)
    listed = _browse(cli, monkeypatch, [("POST /api/folder", {"folder": folder})])
    files = _body(listed[0][0])["files"][:2]
    asked = {
        "action": "add",
        "keys": [f["key"] for f in files],
        "search": {"folder": folder},
    }
    answers, console = _browse(
        cli,
        monkeypatch,
        [("POST /api/chosen", asked), ("POST /api/folder", {"folder": folder})],
    )
    assert json.loads(answers[0].body)["count"] == len(files)
    marked = [file["chosen"] for file in _body(answers[1])["files"]]
    assert marked[:3] == [True, True, False]
    assert "clean --decisions" in console.split("What next")[-1]
    names = [str(file["name"]) for file in files]
    chosen = read_decisions(locations.reports_dir / "decisions.json").chosen
    assert [entry.path.rsplit("\\", 1)[-1] for entry in chosen] == names
    assert {entry.found_by for entry in chosen} == {folder}
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    dcim = locations.data_dir / "c" / "Photos" / "DCIM"
    assert not any((dcim / name).exists() for name in names)
    assert set(names) <= {p.name for p in locations.quarantine_dir.rglob("*.jpg")}


def test_the_pages_refuse_other_hosts_and_serve_both_pages(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Loopback only; `/browse` and `/` link to each other; a folder body is checked."""
    answers: list[Response] = []

    async def attack(app: SearchApp) -> None:
        foreign = {"host": "evil.example", "content-type": "application/json"}
        answers.extend(
            [
                await app.handle(Request("GET", "/api/folders", foreign)),
                await app.handle(Request("GET", "/browse", JSON)),
                await app.handle(Request("GET", "/search", JSON)),
                await app.handle(Request("GET", "/", JSON)),
                await app.handle(Request("POST", "/api/folder", JSON, b'{"x": 1}')),
                await app.handle(Request("GET", "/video/1.mp4", JSON)),
            ]
        )

    monkeypatch.setattr(search_pages, "run_server", fake_server(attack))
    assert run(cli, "browse").exit_code == 0
    browse = answers[1]
    assert [answer.status for answer in answers] == [403, 200, 200, 200, 400, 404]
    assert b"/api/folders" in browse.body
    assert b'href="/search"' in browse.body
    assert answers[3].body == browse.body  # `browse` opens on the folders
    assert "media-src 'self'" in browse.policy
    assert b'href="/browse"' in answers[2].body
