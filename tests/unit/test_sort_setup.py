"""The target, layouts, `leave` and `person_folders` set from the pages (0533)."""

from __future__ import annotations

import json
import sqlite3
import tomllib
from collections import Counter
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.classify.layout import Values
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search.days import NAME as DAY
from media_hygiene.search.folder_role_desk import RoleDesk
from media_hygiene.search.sort_folder_desk import SortFolderDesk
from media_hygiene.search.sort_setup_desk import SortSetupDesk
from media_hygiene.search.sort_setup_preview import MAIN, preview
from tests.support.role_config import PROTECTED_CONFIG

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.review.http import Response

_CONFIG = (
    PROTECTED_CONFIG
    + """[classify]
# my layout
layout = "{year}/{month_name}"

[classify.ai]
model = "x"
"""
)
_DATED = "{year}/{year_month}/{category}"
_MONTHS = "{year}/{year_month}"


def _roles(tmp_path: Path) -> RoleDesk:
    data = tmp_path / "data"
    (data / "c" / "Photos" / "Master").mkdir(parents=True)
    config = tmp_path / "config.toml"
    config.write_text(_CONFIG, "utf-8")
    return RoleDesk(config, HostPathMapper(data), (data / "c",))


@pytest.fixture(name="desk")
def _desk(tmp_path: Path) -> Iterator[SortSetupDesk]:
    index = sqlite3.connect(":memory:")
    index.create_function(DAY, 1, lambda text: text)
    index.execute("CREATE TABLE files (media_date TEXT)")
    days = ("2024-07-01", "2024-07-02", "2023-01-05", None)
    index.executemany("INSERT INTO files VALUES (?)", [(day,) for day in days])
    yield SortSetupDesk(_roles(tmp_path), index, lambda: None)
    index.close()


def _read(answer: Response) -> dict[str, object]:
    return cast("dict[str, object]", json.loads(answer.body))


def _file(desk: SortSetupDesk | SortFolderDesk) -> dict[str, dict[str, object]]:
    text = desk.roles.config_file.read_text("utf-8")
    return tomllib.loads(text)


def _post(desk: SortSetupDesk, target: str, layout: str) -> Response:
    asked = {"target": target, "layouts": {MAIN: layout}}
    return desk.answer(json.dumps(asked).encode())


def test_the_state_says_the_file_and_trees_on_the_photos(desk: SortSetupDesk) -> None:
    """The layout of the file stays offered; the trees count the dated photos."""
    shown = desk.shown()
    assert cast("dict[str, str]", shown["layouts"])[MAIN] == "{year}/{month_name}"
    trees = cast("dict[str, dict[str, dict[str, object]]]", shown["previews"])[MAIN]
    assert set(trees) == {_DATED, _MONTHS, "{year}/{month_name}"}
    assert trees[_MONTHS]["files"] == 3
    assert trees[_MONTHS]["folders"] == 2
    assert trees[_MONTHS]["lines"] == (("2024/2024-07", 2), ("2023/2023-01", 1))
    assert shown["from_plan"] is False


def test_a_model_and_a_target_are_saved_keeping_comments(desk: SortSetupDesk) -> None:
    """Saved in `[classify]`, not its sub-table; comments kept; read back."""
    answer = _post(desk, "C:\\Photos\\Sorted", _MONTHS)
    assert answer.status == HTTPStatus.OK
    saved = _file(desk)["classify"]
    assert saved["layout"] == _MONTHS
    assert saved["target"] == "C:\\Photos\\Sorted"
    assert cast("dict[str, str]", saved["ai"])["model"] == "x"
    text = desk.roles.config_file.read_text("utf-8")
    assert "# my comment" in text
    assert "'C:\\Photos\\Sorted'" in text
    assert _read(answer)["target"] == "C:\\Photos\\Sorted"


def test_another_layout_is_refused_the_file_untouched(desk: SortSetupDesk) -> None:
    """Only the models, or what the file holds, may be posted."""
    before = desk.roles.config_file.read_text("utf-8")
    assert _post(desk, "", "{year}/{place}").status == HTTPStatus.CONFLICT
    assert _post(desk, "", "").status == HTTPStatus.CONFLICT  # the sure one must file
    assert desk.roles.config_file.read_text("utf-8") == before


def test_a_target_outside_or_protected_is_refused(desk: SortSetupDesk) -> None:
    """Not mounted, or inside a protected folder: said, the file unchanged."""
    before = desk.roles.config_file.read_text("utf-8")
    assert _post(desk, "D:\\Elsewhere", _MONTHS).status == HTTPStatus.CONFLICT
    answer = _post(desk, "C:\\Photos\\Master\\x", _MONTHS)
    assert answer.status == HTTPStatus.CONFLICT
    assert "Master" in str(_read(answer)["error"])
    assert desk.roles.config_file.read_text("utf-8") == before


def test_a_body_that_is_not_a_choice_is_refused(desk: SortSetupDesk) -> None:
    """Bad JSON: 400."""
    assert desk.answer(b"{}").status == HTTPStatus.BAD_REQUEST


def test_a_date_only_file_counts_only_without_a_category() -> None:
    """A file only its date places files itself when the layout asks no event."""
    alone = Values(2024, 7, 1)
    pools: dict[str, Counter[Values]] = {"date_only": Counter({alone: 1})}
    assert preview(_MONTHS, MAIN, pools).files == 1
    assert preview(_DATED, MAIN, pools).files == 0


def _folder_post(desk: SortFolderDesk, **asked: object) -> Response:
    return desk.answer(json.dumps(asked).encode())


def test_a_folder_left_out_then_gone_then_removed(tmp_path: Path) -> None:
    """Added; renamed in Explorer it is listed as missing; *Remove* takes it off."""
    roles = _roles(tmp_path)
    desk = SortFolderDesk(roles)
    folder = "C:\\Photos\\Master"
    answer = _folder_post(desk, folder=folder, leave=True)
    assert _read(answer)["leave"] == [{"path": folder, "where": "here"}]
    (tmp_path / "data" / "c" / "Photos" / "Master").rename(
        tmp_path / "data" / "c" / "Photos" / "Renamed"
    )
    listed = cast("list[dict[str, str]]", desk.shown()["leave"])
    assert listed[0]["where"] == "missing"
    assert _read(_folder_post(desk, folder=folder, leave=False))["leave"] == []
    assert _file(desk)["classify"]["leave"] == []


def test_a_person_needs_a_folder_holding_the_name(tmp_path: Path) -> None:
    """Refused when the sort would not see it; accents ignored; forgotten; no double."""
    desk = SortFolderDesk(_roles(tmp_path))
    refused = _folder_post(desk, folder="C:\\Photos\\Vacances", person="Chloé")
    assert refused.status == HTTPStatus.CONFLICT
    folder = "C:\\Photos\\Photos Chloe"
    assert _read(_folder_post(desk, folder=folder, person="Chloé"))["people"] == [
        "Chloé"
    ]
    assert _read(_folder_post(desk, folder=folder, person="chloe"))["people"] == [
        "chloe"
    ]
    assert _read(_folder_post(desk, forget="Chloé"))["people"] == []
    assert _folder_post(desk, leave=[1]).status == HTTPStatus.BAD_REQUEST
