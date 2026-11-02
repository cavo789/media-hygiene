"""A folder's role set from the pages (0532): saved, read back, refused, missing."""

from __future__ import annotations

import json
import tomllib
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search.folder_role_desk import RoleDesk

if TYPE_CHECKING:
    from pathlib import Path

_CONFIG = """# my comment
[folders]
# my protected
protected = ['C:\\Photos']
"""


def _desk(tmp_path: Path) -> RoleDesk:
    data = tmp_path / "data"
    (data / "c" / "Photos" / "Old").mkdir(parents=True)
    (data / "c" / "Phone").mkdir(parents=True)
    config = tmp_path / "config.toml"
    config.write_text(_CONFIG, "utf-8")
    return RoleDesk(config, HostPathMapper(data), (data / "c",))


def _post(
    desk: RoleDesk, folder: str, role: str
) -> tuple[HTTPStatus, dict[str, object]]:
    answer = desk.answer(json.dumps({"folder": folder, "role": role}).encode())
    return HTTPStatus(answer.status), json.loads(answer.body)


def _folders(desk: RoleDesk) -> dict[str, list[str]]:
    with desk.config_file.open("rb") as file:
        found: dict[str, list[str]] = tomllib.load(file)["folders"]
    return found


def test_listed_roles_say_where_each_folder_is(tmp_path: Path) -> None:
    """Listed roles say where each folder is."""
    desk = _desk(tmp_path)
    assert desk.listed() == [
        {"path": "C:\\Photos", "role": "protected", "where": "here"}
    ]


def test_a_role_is_saved_keeping_comments_and_read_back(tmp_path: Path) -> None:
    """A role is saved keeping comments and read back."""
    desk = _desk(tmp_path)
    status, body = _post(desk, "C:\\Phone", "preferred")
    assert status == HTTPStatus.OK
    assert _folders(desk)["preferred"] == ["C:\\Phone"]
    text = desk.config_file.read_text("utf-8")
    assert "# my comment" in text
    assert "# my protected" in text
    assert {"path": "C:\\Phone", "role": "preferred", "where": "here"} in body["roles"]  # type: ignore[operator]
    assert "C:\\Phone" in str(body["said"])
    assert body["stale"]


def test_a_new_role_replaces_the_former_one(tmp_path: Path) -> None:
    """A new role replaces the former one."""
    desk = _desk(tmp_path)
    _post(desk, "c:\\photos", "excluded")  # Windows paths ignore case
    folders = _folders(desk)
    assert folders["protected"] == []
    assert folders["excluded"] == ["c:\\photos"]


def test_none_takes_the_role_away(tmp_path: Path) -> None:
    """None takes the role away."""
    desk = _desk(tmp_path)
    status, body = _post(desk, "C:\\Photos", "none")
    assert status == HTTPStatus.OK
    assert _folders(desk)["protected"] == []
    assert body["roles"] == []


def test_a_clashing_role_is_refused_and_the_file_unchanged(tmp_path: Path) -> None:
    """A clashing role is refused and the file unchanged."""
    desk = _desk(tmp_path)
    status, body = _post(desk, "C:\\Photos\\Old", "backups")
    assert status == HTTPStatus.CONFLICT
    assert "folders.backups" in str(body["error"])
    assert desk.config_file.read_text("utf-8") == _CONFIG


def test_a_folder_renamed_in_explorer_is_missing_then_removed(tmp_path: Path) -> None:
    """A folder renamed in explorer is missing then removed."""
    desk = _desk(tmp_path)
    data = tmp_path / "data" / "c"
    (data / "Photos").rename(data / "Pictures")
    assert desk.listed()[0]["where"] == "missing"
    status, _body = _post(desk, "C:\\Photos", "none")
    assert status == HTTPStatus.OK
    assert desk.listed() == []


def test_a_folder_outside_the_mounted_ones_is_elsewhere(tmp_path: Path) -> None:
    """A folder outside the mounted ones is elsewhere."""
    desk = _desk(tmp_path)
    _post(desk, "D:\\Backup", "backups")
    assert {
        "path": "D:\\Backup",
        "role": "backups",
        "where": "elsewhere",
    } in desk.listed()


def test_an_unknown_role_is_a_bad_request(tmp_path: Path) -> None:
    """An unknown role is a bad request."""
    desk = _desk(tmp_path)
    status, _body = _post(desk, "C:\\Photos", "master")
    assert status == HTTPStatus.BAD_REQUEST
