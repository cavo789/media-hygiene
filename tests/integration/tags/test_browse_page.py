"""`browse`: the tree of the folders, the files of one, set aside, then cleaned."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

from media_hygiene.cli.home_state import home_state
from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.home_views import STEP_EXIT_BASE
from media_hygiene.review.http import Request
from media_hygiene.services import search_pages
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from tests.integration.tags.test_search_command import _call, fake_server
from tests.support.cli import run
from tests.support.places_map import JSON
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner, Result

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

    monkeypatch.setattr(search_pages, "serve_until_ended", fake_server(browse))
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

    monkeypatch.setattr(search_pages, "serve_until_ended", fake_server(attack))
    assert run(cli, "browse").exit_code == 0
    browse = answers[1]
    assert [answer.status for answer in answers] == [403, 200, 200, 200, 400, 404]
    assert b"/api/folders" in browse.body
    assert b'href="/search"' in browse.body
    assert answers[3].body == browse.body  # `browse` opens on the folders
    assert "media-src 'self'" in browse.policy
    assert b'href="/browse"' in answers[2].body


def _opened(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, object]]
) -> tuple[list[Response], Result]:
    """Open the folder view, send the calls, stop it; answers and the whole result."""
    answers: list[Response] = []

    async def browse(app: SearchApp) -> None:
        for route, body in calls:
            answers.append(await _call(app, route, body))

    monkeypatch.setattr(search_pages, "serve_until_ended", fake_server(browse))
    return answers, run(cli, "browse")


def _one_set_aside(cli: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the first file of the events' folder aside, from the page."""
    folder = _dcim(cli, monkeypatch)
    listed = _browse(cli, monkeypatch, [("POST /api/folder", {"folder": folder})])
    key = _body(listed[0][0])["files"][0]["key"]
    asked = {"action": "add", "keys": [key], "search": {"folder": folder}}
    assert (
        json.loads(_browse(cli, monkeypatch, [("POST /api/chosen", asked)])[0][0].body)[
            "count"
        ]
        == 1
    )


def test_apply_now_from_home_ends_on_the_clean_step(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0243: opened from home with a choice: the button, the home step's exit code."""
    _one_set_aside(cli, monkeypatch)
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, "1")
    answers, result = _opened(
        cli, monkeypatch, [("GET /browse", None), ("POST /api/apply", {})]
    )
    page, applied = answers[0], answers[1]
    assert b'id="applyNow"' in page.body  # apply_now.html.j2, shared with the reviews
    assert b"window.mhApplyNow" in page.body
    assert applied.status == 200
    step = json.loads(applied.body)
    command = home_state(make_runtime(locations)).command_of(step["number"])
    assert command is not None
    assert command == step["command"]
    assert "--decisions" in command
    assert result.exit_code == STEP_EXIT_BASE + step["number"], result.output
    assert f"Apply now, chosen on the page: {command}" in " ".join(
        result.output.split()
    )
    assert "What next" not in result.output  # mh runs the step: no line to type


def test_apply_now_refused_when_opened_directly(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0243: `mh browse` alone: no button, refused; the next step line stays."""
    _one_set_aside(cli, monkeypatch)
    monkeypatch.delenv(LAUNCHER_STEPS_VARIABLE, raising=False)
    answers, result = _opened(
        cli, monkeypatch, [("GET /browse", None), ("POST /api/apply", {})]
    )
    assert b'id="applyNow"' not in answers[0].body
    assert answers[1].status == 409
    assert result.exit_code == 0, result.output
    assert "clean --decisions" in result.output.split("What next")[-1]


def test_apply_now_refused_with_nothing_set_aside(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0243: opened from home, nothing chosen: refused, the page keeps running."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, "1")
    answers, result = _opened(cli, monkeypatch, [("POST /api/apply", {})])
    assert answers[0].status == 409
    assert json.loads(answers[0].body)["error"] == "Nothing set aside."
    assert result.exit_code == 0, result.output


def test_the_page_lists_its_keys_and_picks_many_at_once(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The keys under the tree, as on the reviews; invert, tick boxes, the rectangle."""
    answers, _ = _browse(cli, monkeypatch, [("GET /browse", None)])
    page = answers[0].body.decode()
    keys = page.split('id="keys"')[1].split("</section>")[0]
    for key in ("<kbd>Shift</kbd>", "<kbd>I</kbd>", "<kbd>Delete</kbd>", "rectangle"):
        assert key in keys
    assert 'id="toc"' in page  # review_side.css.j2: the tree above, the keys below
    assert 'id="invert"' in page
    assert "function invert()" in page
    assert 'element("input", "tick")' in page
    assert 'addEventListener("pointerdown"' in page  # browse_band.js.j2
    assert "Ctrl+click adds one" not in page  # the old line of text is gone


def test_one_bar_above_the_grid_and_the_safety_line_under_the_keys(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0305: one bar, the folder or what to do with the picking; 🔒 in the keys."""
    answers, _ = _browse(cli, monkeypatch, [("GET /browse", None)])
    page = answers[0].body.decode()
    header = page.split('<header id="bar">')[1].split("</header>")[0]
    for part in (
        'id="status"',
        '<span id="acting" hidden>',
        'id="setAside"',
        'id="chosen"',
    ):
        assert part in header
    assert '<button id="takeBack" class="plain" type="button" hidden>' in header
    assert 'id="albumBar"' in header
    # The compact album field says how to start.
    assert "type a name, e.g. Crete 2023" in header
    keys = page.split('id="keys"')[1].split("</section>")[0]
    assert "🔒 Nothing is deleted from this page" in keys
    views = page.split('id="views"')[1].split("</div>")[0]
    assert 'aria-current="page"' in views
    assert 'href="/search"' in views
    script = page.split("function showPicked()")[1].split("\n}\n")[0]
    assert '$("bar").classList.toggle("acting", some)' in script
    # *Take out of the set aside* shows only for a picked file already set aside.
    assert "file.chosen && picked.has(file.key)" in script
