"""`table_of`: every way to write a table keeps its other keys through a save (0584)."""

from __future__ import annotations

import asyncio
import json
import tomllib
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.cli.home_favourites import read_favourites, save_favourites
from media_hygiene.places.toml_edit import document_of, table_of
from media_hygiene.review.home_app import FAVOURITES_PATH
from media_hygiene.review.home_favourites_api import favourites_response
from media_hygiene.review.http import Request

if TYPE_CHECKING:
    from pathlib import Path

_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}
_SPLIT: Final = "[home]\nkept = 1\n[scan]\nother = 2\n[home.more]\nc = 3\n"


@pytest.mark.parametrize(
    ("text", "kept"),
    [
        (_SPLIT, {"kept": 1, "more": {"c": 3}}),
        ("home.kept = 1\nother = 2\n", {"kept": 1}),
        ("home = {kept = 1}\n", {"kept": 1}),
        ("[home.more]\nc = 3\n", {"more": {"c": 3}}),
    ],
    ids=["split", "dotted", "inline", "super"],
)
def test_a_save_keeps_every_other_key(
    tmp_path: Path, text: str, kept: dict[str, object]
) -> None:
    """The star is written, nothing else of the table is lost."""
    config = tmp_path / "config.toml"
    config.write_text(text, "utf-8")
    assert save_favourites(config, ("search",)) == ("search",)
    assert read_favourites(config) == ("search",)
    read_back = tomllib.loads(config.read_text("utf-8"))
    assert read_back["home"] == {**kept, "favorites": ["search"]}


def test_a_split_table_keeps_the_section_between(tmp_path: Path) -> None:
    """The section in the middle of a split table stays."""
    config = tmp_path / "config.toml"
    config.write_text(_SPLIT, "utf-8")
    save_favourites(config, ("audit",))
    assert tomllib.loads(config.read_text("utf-8"))["scan"] == {"other": 2}


def test_a_value_that_is_not_a_table_is_refused_never_overwritten(
    tmp_path: Path,
) -> None:
    """`home = 3` is a mistake to say, not a value to replace."""
    config = tmp_path / "config.toml"
    config.write_text("home = 3\n", "utf-8")
    with pytest.raises(ValueError, match="home"):
        table_of(document_of(config), "home")


def _post(config: Path) -> tuple[HTTPStatus, str]:
    """Star an action as the page does; the status and the sentence answered."""
    body = json.dumps({"names": ["audit"]}).encode()
    reply = asyncio.run(
        favourites_response(config, Request("POST", FAVOURITES_PATH, _JSON, body))
    )
    return reply.status, json.loads(reply.body)["error"]


def test_a_broken_file_says_it_cannot_be_read_and_logs(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Invalid TOML: the sentence names the reading, the log has the exception."""
    config = tmp_path / "config.toml"
    config.write_text("[home\n", "utf-8")
    status, said = _post(config)
    assert status is HTTPStatus.INTERNAL_SERVER_ERROR
    assert "cannot be read" in said
    assert caplog.records[-1].exc_info is not None
    assert config.read_text("utf-8") == "[home\n"


def test_a_file_that_cannot_be_written_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An `OSError` of the write: the other sentence."""
    config = tmp_path / "config.toml"

    def refuse(*_args: object) -> None:
        raise PermissionError

    monkeypatch.setattr(
        "media_hygiene.review.home_favourites_api.save_favourites", refuse
    )
    status, said = _post(config)
    assert status is HTTPStatus.INTERNAL_SERVER_ERROR
    assert "cannot be written" in said
