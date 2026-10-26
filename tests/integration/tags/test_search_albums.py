"""Albums from `search` and `browse` (0295): apart from *Set aside*, saved, read back.

An album and the files set aside never touch each other's list; an album's file sent
to the quarantine by `clean --decisions` is said missing, and is back after `undo`.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.share.albums import ALBUMS_FILE, read_albums
from tests.support.cli import run
from tests.support.search_page import serve_search

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response

_DURBUY: Final = {"text": "durbuy"}
_ALBUM: Final = "Durbuy 2022"


def _add(**more: object) -> tuple[str, object]:
    """`POST /api/albums`, adding to the album."""
    return ("POST /api/albums", {"action": "add", "album": _ALBUM, **more})


def _albums(answer: Response) -> list[dict[str, object]]:
    """The albums an answer lists."""
    albums: list[dict[str, object]] = json.loads(answer.body)["albums"]
    return albums


def test_an_album_and_the_set_aside_never_touch_each_other(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Adding to an album writes no decision; setting aside changes no album."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    decisions = locations.reports_dir / "decisions.json"
    albums = locations.reports_dir / ALBUMS_FILE
    first = serve_search(cli, monkeypatch, [("POST /api/search", _DURBUY)])
    key = json.loads(first[0].body)["hits"][0]["key"]
    answers = serve_search(
        cli,
        monkeypatch,
        [
            ("GET /api/albums", None),
            _add(keys=[str(key)], search=_DURBUY),
            _add(all=True, search=_DURBUY),
        ],
    )
    assert "No album yet" in json.loads(answers[0].body)["message"]
    assert [album["count"] for album in _albums(answers[1]) + _albums(answers[2])] == [
        1,
        3,
    ]
    assert "Only this file changed" in json.loads(answers[2].body)["message"]
    assert not decisions.exists()
    saved = albums.read_bytes()
    chosen = serve_search(
        cli,
        monkeypatch,
        [("POST /api/chosen", {"action": "add", "all": True, "search": _DURBUY})],
    )
    assert json.loads(chosen[0].body)["count"] == 3
    assert albums.read_bytes() == saved
    removed = serve_search(
        cli,
        monkeypatch,
        [("POST /api/albums", {"action": "remove", "album": _ALBUM, "all": True})],
    )
    assert _albums(removed[0]) == []
    assert "is empty: removed" in json.loads(removed[0].body)["message"]
    assert len(json.loads(decisions.read_text())["chosen"]) == 3


def test_a_bad_request_or_name_saves_nothing(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """400 for a body that is not a change; 409, said, for a name with quotes."""
    answers = serve_search(
        cli,
        monkeypatch,
        [
            ("POST /api/albums", {"action": "keep", "album": _ALBUM}),
            ("POST /api/albums", {"action": "add", "album": 'A "b"', "all": True}),
        ],
    )
    assert [answer.status for answer in answers] == [400, 409]
    assert "double quotes" in json.loads(answers[1].body)["error"]
    assert not (locations.reports_dir / ALBUMS_FILE).exists()


def test_an_album_file_in_quarantine_is_missing_then_back_after_undo(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`clean --decisions` moves a file of the album: said missing, kept; `undo`."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    first = serve_search(cli, monkeypatch, [("POST /api/search", _DURBUY)])
    key = str(json.loads(first[0].body)["hits"][0]["key"])
    serve_search(
        cli,
        monkeypatch,
        [
            _add(all=True, search=_DURBUY),
            ("POST /api/chosen", {"action": "add", "keys": [int(key)]}),
        ],
    )
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    [gone] = _albums(serve_search(cli, monkeypatch, [("GET /api/albums", None)])[0])
    assert gone["count"] == 3
    assert len(gone["missing"]) == 1  # type: ignore[arg-type]
    assert run(cli, "undo").exit_code == 0
    [back] = _albums(serve_search(cli, monkeypatch, [("GET /api/albums", None)])[0])
    assert back["missing"] == []
    (album,) = read_albums(locations.reports_dir / ALBUMS_FILE).albums
    assert len(album.entries) == 3


def test_the_pages_carry_the_album_bar(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Search and browse: *Add to the album* and *Share on the TV*, apart."""
    answers = serve_search(
        cli, monkeypatch, [("GET /search", None), ("GET /browse", None)]
    )
    for answer in answers:
        assert b'id="albumAdd"' in answer.body
        assert b'id="albumTv"' in answer.body
        assert b"/api/albums" in answer.body
        assert b'id="setAside"' in answer.body
