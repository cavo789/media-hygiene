"""0784: the *Versions* page lists each file's versions and restores one."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

from media_hygiene.file_history import replace_text, versions_of
from media_hygiene.paths.locations import Locations
from media_hygiene.review.http import Request
from media_hygiene.services.settings_here import SettingsHere
from media_hygiene.services.settings_versions import saved_files
from media_hygiene.services.versions_here import (
    RESTORE_PATH,
    VERSIONS_PAGE,
    VersionsHere,
)
from media_hygiene.share.albums import ALBUMS_FILE

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.fresh_runtime import FreshRuntime

_HOST = {"host": "127.0.0.1", "content-type": "application/json"}


def _here(tmp_path: Path) -> tuple[VersionsHere, Locations]:
    locations = Locations(
        config_dir=tmp_path / "config", reports_dir=tmp_path / "reports"
    )
    locations.config_dir.mkdir()
    locations.reports_dir.mkdir()
    runtime = type("R", (), {"locations": locations})()
    fresh = cast("FreshRuntime", type("F", (), {"runtime": lambda _self: runtime})())
    return VersionsHere(fresh), locations


def _post(
    here: VersionsHere, body: dict[str, str]
) -> tuple[HTTPStatus, dict[str, object]]:
    request = Request("POST", RESTORE_PATH, _HOST, json.dumps(body).encode())
    response = asyncio.run(here.handle(request))
    return response.status, json.loads(response.body)


def _saved(path: Path, *contents: str) -> None:
    for content in contents:
        replace_text(path, content)


def test_each_file_kind_is_restored_byte_identical_then_undone(tmp_path: Path) -> None:
    """config.toml, a person, an event, albums.json: Restore, then its Undo."""
    here, locations = _here(tmp_path)
    config = locations.config_file
    person = locations.config_dir / "people" / "ann.toml"
    event = locations.config_dir / "events" / "2026.toml"
    albums = locations.reports_dir / ALBUMS_FILE
    person.parent.mkdir()
    event.parent.mkdir()
    _saved(config, "[clean]\npurge_hint_days = 30\n", "[clean]\npurge_hint_days = 9\n")
    for path, first, second in (
        (person, 'name = "Ann"\n', 'name = "Anne"\n'),
        (event, "[[rules]]\nx = 1\n", "[[rules]]\nx = 2\n"),
        (albums, '{"albums": []}', '{"albums": [1]}'),
    ):
        _saved(path, first, second)
    listed = {each.label: each for each in saved_files(locations)}
    assert next(iter(listed)) == "config.toml"
    assert listed["config.toml"].versions[0].keys == ("clean.purge_hint_days",)
    for path in (config, person, event, albums):
        _restore_then_undo(here, path)


def _restore_then_undo(here: VersionsHere, path: Path) -> None:
    """The newest version restored, read back; its Undo: byte-identical to before."""
    before = path.read_bytes()
    older = versions_of(path)[0]
    wanted = older.read_bytes()
    status, answer = _post(here, {"path": str(path), "name": older.name})
    assert status is HTTPStatus.OK
    assert path.read_bytes() == wanted
    assert answer["content"] == wanted.decode()
    status, _undone = _post(here, {"path": str(path), "name": str(answer["kept"])})
    assert status is HTTPStatus.OK
    assert path.read_bytes() == before


def test_a_trimmed_version_or_an_unlisted_path_is_refused(tmp_path: Path) -> None:
    """409, said, nothing changed; a bad body 400; the page renders; GET only."""
    here, locations = _here(tmp_path)
    config = locations.config_file
    _saved(config, "a = 1\n", "a = 2\n")
    version = versions_of(config)[0]
    version.unlink()  # trimmed meanwhile
    status, answer = _post(here, {"path": str(config), "name": version.name})
    assert status is HTTPStatus.CONFLICT
    assert answer["error"]
    assert config.read_text("utf-8") == "a = 2\n"
    outside = tmp_path / "elsewhere.toml"
    status, _answer = _post(here, {"path": str(outside), "name": version.name})
    assert status is HTTPStatus.CONFLICT
    bad = asyncio.run(here.handle(Request("POST", RESTORE_PATH, _HOST, b"{}")))
    assert bad.status is HTTPStatus.BAD_REQUEST
    page = asyncio.run(here.handle(Request("GET", VERSIONS_PAGE, _HOST, b"")))
    assert page.status is HTTPStatus.OK
    assert b"mhUndoToast" in page.body
    assert here.serves(VERSIONS_PAGE)
    assert not SettingsHere.serves(VERSIONS_PAGE)
