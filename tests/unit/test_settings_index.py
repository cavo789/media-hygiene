"""The settings index (0670): every group, values read from disk, the rest counted."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.review.http import Request
from media_hygiene.review.setting_groups import EVENTS_PATH, GROUPS
from media_hygiene.services.settings_here import (
    SETTINGS_PAGE,
    SettingsHere,
    settings_page,
)
from media_hygiene.services.settings_index import config_only, leaf_keys, shown_values
from media_hygiene.services.settings_rows import setting_rows

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.fresh_runtime import FreshRuntime

_HOSTILE = "<img src=x onerror=alert(1)>"


def test_every_group_of_setting_groups_has_its_row() -> None:
    """A new group of `setting_groups.py` fails here until the index lists it."""
    rows = {row.group: row for row in setting_rows() if row.group}
    assert set(GROUPS) == set(rows)
    for path, group in GROUPS.items():
        named = {key.rsplit(".", 1)[-1] for key in rows[path].keys}
        assert {field.key for field in group.fields} == named


def test_every_key_a_row_names_is_a_setting() -> None:
    """A row never names a key the settings do not load."""
    known = set(leaf_keys())
    for row in setting_rows():
        assert set(row.keys) <= known, row.title


def test_config_only_is_the_rest_of_the_model() -> None:
    """Every key is either on a page or in the config.toml-only list."""
    rows = setting_rows()
    only = config_only(rows)
    named = {key for row in rows for key in row.keys}
    assert only
    assert not named & set(only)
    assert named | set(only) == set(leaf_keys())


def test_a_value_is_read_from_the_disk_or_the_default(tmp_path: Path) -> None:
    """The file's value is shown; a missing key shows the default, marked."""
    config = tmp_path / "config.toml"
    config.write_text("[classify]\nmin_event_size = 7\n", encoding="utf-8")
    events = next(row for row in setting_rows() if row.group == EVENTS_PATH)
    values = {one.key: one for one in shown_values(config, events)}
    assert values["classify.min_event_size"].value == "7"
    assert not values["classify.min_event_size"].default
    assert values["classify.merge_gap_hours"].default


def test_the_page_lists_every_row_and_escapes_values(tmp_path: Path) -> None:
    """Each title is on the page, the count of the rest, a hostile value as text."""
    config = tmp_path / "config.toml"
    config.write_text(f'[album]\nroot = "{_HOSTILE}"\n', encoding="utf-8")
    page = settings_page(config).decode()
    for row in setting_rows():
        assert row.href in page
    assert str(len(config_only(setting_rows()))) in page
    assert _HOSTILE not in page
    assert "&lt;img" in page


def _request(path: str, method: str = "GET") -> Request:
    """A loopback request."""
    return Request(method, path, {"host": "127.0.0.1"}, b"")


def test_the_route_serves_the_page_and_writes_nothing(tmp_path: Path) -> None:
    """`GET` the page, the prefix redirected, any other method refused."""
    runtime = SimpleNamespace(
        locations=SimpleNamespace(config_file=tmp_path / "c.toml")
    )
    fresh = cast("FreshRuntime", SimpleNamespace(runtime=lambda: runtime))
    here = SettingsHere(fresh)
    assert here.serves(SETTINGS_PAGE)
    assert not here.serves("/settingsx")
    got = asyncio.run(here.handle(_request(SETTINGS_PAGE)))
    assert got.status is HTTPStatus.OK
    moved = asyncio.run(here.handle(_request(SETTINGS_PAGE.rstrip("/"))))
    assert moved.status is HTTPStatus.SEE_OTHER
    posted = asyncio.run(here.handle(_request(SETTINGS_PAGE, "POST")))
    assert posted.status is HTTPStatus.METHOD_NOT_ALLOWED
    assert not (tmp_path / "c.toml").exists()
