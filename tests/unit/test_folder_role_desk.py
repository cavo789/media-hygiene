"""A folder's role set from the pages (0532): saved, read back, refused, missing."""

from __future__ import annotations

import dataclasses
import json
import sqlite3
import tomllib
from contextlib import closing
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search.folder_role_desk import RoleDesk

if TYPE_CHECKING:
    from collections.abc import Iterator
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
        {"path": "C:\\Photos", "role": "protected", "where": "here", "carry": []}
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
    assert {
        "path": "C:\\Phone",
        "role": "preferred",
        "where": "here",
        "carry": [],
    } in body["roles"]  # type: ignore[operator]
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
    assert not desk.listed()


def test_a_folder_outside_the_mounted_ones_is_elsewhere(tmp_path: Path) -> None:
    """A folder outside the mounted ones is elsewhere."""
    desk = _desk(tmp_path)
    _post(desk, "D:\\Backup", "backups")
    assert {
        "path": "D:\\Backup",
        "role": "backups",
        "where": "elsewhere",
        "carry": [],
    } in desk.listed()


def test_an_unknown_role_is_a_bad_request(tmp_path: Path) -> None:
    """An unknown role is a bad request."""
    desk = _desk(tmp_path)
    status, _body = _post(desk, "C:\\Photos", "master")
    assert status == HTTPStatus.BAD_REQUEST


def test_excluded_inside_protected_is_refused_file_unchanged(tmp_path: Path) -> None:
    """An excluded folder inside a protected one is refused, its reason said (0581)."""
    desk = _desk(tmp_path)
    status, body = _post(desk, "C:\\Photos\\Old", "excluded")
    assert status == HTTPStatus.CONFLICT
    assert "folders.excluded" in str(body["error"])
    assert desk.config_file.read_text("utf-8") == _CONFIG


def test_protected_inside_excluded_is_refused_file_unchanged(tmp_path: Path) -> None:
    """A protected folder inside an excluded one is refused too (0581)."""
    desk = _desk(tmp_path)
    config = "[folders]\nexcluded = ['C:\\\\Phone']\n"
    desk.config_file.write_text(config, "utf-8")
    (tmp_path / "data" / "c" / "Phone" / "Keep").mkdir()
    status, body = _post(desk, "C:\\Phone\\Keep", "protected")
    assert status == HTTPStatus.CONFLICT
    assert "folders.protected" in str(body["error"])
    assert desk.config_file.read_text("utf-8") == config


@pytest.fixture
def index() -> Iterator[sqlite3.Connection]:
    """An index of the files alone, closed after the test."""
    with closing(sqlite3.connect(":memory:")) as connection:
        yield connection


def _indexed(
    desk: RoleDesk, index: sqlite3.Connection, folders: tuple[str, ...]
) -> RoleDesk:
    """An index holding the same two files in each folder (container paths)."""
    index.execute(
        "CREATE TABLE files (path TEXT PRIMARY KEY, size INTEGER NOT NULL,"
        " partial_digest TEXT, full_digest TEXT)"
    )
    for folder in folders:
        for name, size, digest in (("a.jpg", 10, "aa"), ("Old/b.jpg", 20, "bb")):
            index.execute(
                "INSERT INTO files VALUES (?, ?, ?, ?)",
                (f"{folder}/{name}", size, digest[0], digest),
            )
    return dataclasses.replace(desk, index=index)


def _rename(tmp_path: Path, *to: str) -> None:
    data = tmp_path / "data" / "c"
    for index, name in enumerate(to):
        if index == 0:
            (data / "Photos").rename(data / name)
        else:
            (data / name).mkdir()


def test_a_folder_renamed_offers_to_carry_its_role(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """0580: same files below a new name: the role moves there, read back."""
    data = tmp_path / "data" / "c"
    desk = _indexed(_desk(tmp_path), index, (f"{data}/Photos", f"{data}/Pictures"))
    _rename(tmp_path, "Pictures")
    assert desk.listed()[0]["carry"] == ["C:\\Pictures"]
    answer = desk.answer(
        json.dumps(
            {"folder": "C:\\Pictures", "role": "protected", "former": "C:\\Photos"}
        ).encode()
    )
    assert answer.status == HTTPStatus.OK
    assert _folders(desk)["protected"] == ["C:\\Pictures"]
    assert desk.listed()[0]["where"] == "here"


def test_a_folder_deleted_has_no_candidate(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """0580: the files are nowhere else: only *Remove*."""
    data = tmp_path / "data" / "c"
    desk = _indexed(_desk(tmp_path), index, (f"{data}/Photos",))
    _rename(tmp_path, "Gone")
    assert desk.listed()[0]["carry"] == []


def test_two_candidates_are_both_listed(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """0580: a copy of the folder too: both offered, none chosen."""
    data = tmp_path / "data" / "c"
    folders = (f"{data}/Photos", f"{data}/Pictures", f"{data}/Copy")
    desk = _indexed(_desk(tmp_path), index, folders)
    _rename(tmp_path, "Pictures", "Copy")
    assert desk.listed()[0]["carry"] == ["C:\\Copy", "C:\\Pictures"]
