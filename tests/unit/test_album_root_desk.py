"""The albums' folder said and changed from the album bar (0534)."""

from __future__ import annotations

import json
import sqlite3
import tomllib
from contextlib import closing
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search.album_root_desk import AlbumRootDesk
from media_hygiene.search.album_root_tree import folders_response
from media_hygiene.search.folder_role_desk import RoleDesk
from tests.support.role_config import PROTECTED_CONFIG

if TYPE_CHECKING:
    from pathlib import Path

_CONFIG = (
    PROTECTED_CONFIG
    + """[classify]
target = 'C:\\\\Photos\\\\Sorted'
"""
)


def _desk(tmp_path: Path) -> AlbumRootDesk:
    data = tmp_path / "data"
    (data / "c" / "Photos" / "Master").mkdir(parents=True)
    config = tmp_path / "config.toml"
    config.write_text(_CONFIG, "utf-8")
    return AlbumRootDesk(RoleDesk(config, HostPathMapper(data), (data / "c",)))


def _post(desk: AlbumRootDesk, root: str) -> tuple[HTTPStatus, dict[str, object]]:
    answer = desk.answer(json.dumps({"root": root}).encode())
    return HTTPStatus(answer.status), json.loads(answer.body)


def test_empty_root_says_the_default_folder(tmp_path: Path) -> None:
    """Empty root says the default folder."""
    shown = _desk(tmp_path).shown()
    assert shown == {"root": "", "used": "C:\\Photos\\Sorted\\_Albums"}


def test_a_root_is_saved_keeping_comments_and_read_back(tmp_path: Path) -> None:
    """A root is saved keeping comments and read back."""
    desk = _desk(tmp_path)
    status, body = _post(desk, "C:\\Photos\\Albums")
    assert status == HTTPStatus.OK
    text = desk.roles.config_file.read_text("utf-8")
    assert "# my comment" in text
    assert tomllib.loads(text)["album"]["root"] == "C:\\Photos\\Albums"
    assert body["used"] == "C:\\Photos\\Albums"
    assert body["old"] == "C:\\Photos\\Sorted\\_Albums"  # the former folder
    assert body["movable"] == 0  # no album folder made there: no move offered


def test_a_protected_or_unmounted_root_is_refused(tmp_path: Path) -> None:
    """A protected or unmounted root is refused, the file unchanged."""
    desk = _desk(tmp_path)
    for root in ("C:\\Photos\\Master\\Albums", "D:\\Albums"):
        status, body = _post(desk, root)
        assert status == HTTPStatus.CONFLICT
        assert root in str(body["error"])
    assert desk.roles.config_file.read_text("utf-8") == _CONFIG


def test_a_control_character_is_a_bad_request(tmp_path: Path) -> None:
    """A control character is a bad request."""
    status, _body = _post(_desk(tmp_path), "C:\\Photos\x08")
    assert status == HTTPStatus.BAD_REQUEST


def test_the_state_lists_the_mounted_drives_to_pick_from(tmp_path: Path) -> None:
    """0797: the page's chooser lists the mounted folders, as the host names them."""
    state = json.loads(_desk(tmp_path).state().body)
    assert state["mounts"] == ["C:\\"]
    assert state["used"] == "C:\\Photos\\Sorted\\_Albums"


def test_the_folders_tree_is_the_librarys_from_the_index(tmp_path: Path) -> None:
    """The chooser's tree holds the index's folders, host names, as the library's."""
    data = tmp_path / "data"
    photos = data / "c" / "Photos" / "Master"
    photos.mkdir(parents=True)
    index = tmp_path / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        connection.execute("CREATE TABLE files (path TEXT, size INTEGER)")
        connection.execute("INSERT INTO files VALUES (?, 10)", (str(photos / "a.jpg"),))
        connection.commit()
    mapper = HostPathMapper(data)
    answer = folders_response(index, mapper, (data / "c",))
    folders = json.loads(answer.body)["folders"]
    assert [folder["path"] for folder in folders][-1] == "C:\\Photos\\Master"
    assert folders[-1]["photos"] == 1
    assert json.loads(folders_response(None, mapper, ()).body) == {"folders": []}
    broken = tmp_path / "broken.sqlite"
    broken.write_text("not a database", "utf-8")
    assert json.loads(folders_response(broken, mapper, ()).body) == {"folders": []}
