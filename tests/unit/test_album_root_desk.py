"""The albums' folder said and changed from the album bar (0534)."""

from __future__ import annotations

import json
import tomllib
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search.album_root_desk import AlbumRootDesk, folder_gets
from media_hygiene.search.folder_role_desk import ALBUM_ROOT_PATH, RoleDesk
from media_hygiene.search.folders import FOLDERS_PATH, FolderDesk

if TYPE_CHECKING:
    from pathlib import Path

_CONFIG = """# my comment
[folders]
protected = ['C:\\\\Photos\\\\Master']

[classify]
target = 'C:\\\\Photos\\\\Sorted'
"""


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
    assert shown == {"root": "", "used": "C:\\Photos\\Sorted\\Albums"}


def test_a_root_is_saved_keeping_comments_and_read_back(tmp_path: Path) -> None:
    """A root is saved keeping comments and read back."""
    desk = _desk(tmp_path)
    status, body = _post(desk, "C:\\Photos\\Albums")
    assert status == HTTPStatus.OK
    text = desk.roles.config_file.read_text("utf-8")
    assert "# my comment" in text
    assert tomllib.loads(text)["album"]["root"] == "C:\\Photos\\Albums"
    assert body["used"] == "C:\\Photos\\Albums"
    assert body["old"] == "C:\\Photos\\Sorted\\Albums"  # the former folder
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


def test_the_routes_are_served_by_the_folder_view(tmp_path: Path) -> None:
    """The routes are served by the folder view."""
    desk = _desk(tmp_path)
    roles = desk.roles
    folders = FolderDesk(None, roles.mapper, roles.roots, None, roles, desk)  # type: ignore[arg-type]
    gets = folder_gets(folders)
    assert set(gets) == {FOLDERS_PATH, ALBUM_ROOT_PATH}
    assert json.loads(gets[ALBUM_ROOT_PATH]().body)["root"] == ""
    answer = folders.answer(ALBUM_ROOT_PATH, b'{"root": ""}')
    assert answer.status == HTTPStatus.OK
