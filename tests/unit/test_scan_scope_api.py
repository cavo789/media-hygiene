"""What the audit analyses and ignores, changed from the home page (0535)."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.places.toml_edit import loaded
from media_hygiene.review.http import Request
from media_hygiene.review.lan_paths import READ_PATHS
from media_hygiene.review.scan_scope_api import SCOPE_PATH, scope_of, scope_route
from media_hygiene.review.write_routes import CHANGES
from media_hygiene.services.home import home_page

if TYPE_CHECKING:
    from pathlib import Path

_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}
_COMMENTED: Final = "# mine\n[scan]\n# keep me\nextensions = ['photo', '.heic']\n"


def _ask(
    config_file: Path, method: str, body: object = None
) -> tuple[HTTPStatus, dict[str, object]]:
    """Send a request as the page does."""
    data = b"" if body is None else json.dumps(body).encode()
    request = Request(method, SCOPE_PATH, _JSON, data)
    reply = asyncio.run(scope_route(config_file, request))
    return reply.status, json.loads(reply.body or b"{}")


def test_no_file_means_everything_analysed(tmp_path: Path) -> None:
    """Nothing written: every kind, no folder name ignored."""
    status, answer = _ask(tmp_path / "config.toml", "GET")
    assert status == HTTPStatus.OK
    assert answer["scope"] == {
        "kinds": ["photo", "raw", "video"],
        "others": [],
        "names": [],
    }


def test_a_change_is_written_read_back_and_said_stale(tmp_path: Path) -> None:
    """Comments and hand-written extensions kept; the answer is the file's."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(_COMMENTED, encoding="utf-8")
    body = {"kinds": ["photo", "video"], "names": ["Thumbs", " ", "@eaDir"]}
    status, answer = _ask(config_file, "POST", body)
    assert status == HTTPStatus.OK
    assert answer["scope"] == {
        "kinds": ["photo", "video"],
        "others": [".heic"],
        "names": ["Thumbs", "@eaDir"],
    }
    assert answer["stale"]
    text = config_file.read_text(encoding="utf-8")
    assert "# keep me" in text
    assert loaded(config_file)["scan"]["extensions"] == ["photo", "video", ".heic"]


def test_every_kind_ticked_writes_every_media_file(tmp_path: Path) -> None:
    """All three ticked: no extension list, as by default (hand-written ones too)."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(_COMMENTED, encoding="utf-8")
    status, _answer = _ask(config_file, "POST", {"kinds": ["photo", "raw", "video"]})
    assert status == HTTPStatus.OK
    assert loaded(config_file)["scan"]["extensions"] == []
    assert scope_of(config_file)["kinds"] == ["photo", "raw", "video"]


def test_no_kind_or_a_path_as_name_is_refused_file_unchanged(tmp_path: Path) -> None:
    """Nothing ticked: 400; a path for a name: 409; the file as it was."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(_COMMENTED, encoding="utf-8")
    assert _ask(config_file, "POST", {"kinds": []})[0] == HTTPStatus.BAD_REQUEST
    status, answer = _ask(config_file, "POST", {"kinds": ["photo"], "names": ["a/b"]})
    assert status == HTTPStatus.CONFLICT
    assert answer["error"]
    assert config_file.read_text(encoding="utf-8") == _COMMENTED


def test_the_route_writes_from_the_pc_only_and_the_page_shows_it() -> None:
    """A phone never reaches it; the home page draws the line and its form."""
    assert SCOPE_PATH in CHANGES
    assert SCOPE_PATH not in READ_PATHS
    page = home_page().decode()
    assert "scopeHtml()" in page
    assert SCOPE_PATH in page
