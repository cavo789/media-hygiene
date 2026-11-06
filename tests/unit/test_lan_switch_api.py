"""`[review] lan` and `lan_phone_originals` switched from the home page (0605)."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.config.review_settings import ReviewSettings
from media_hygiene.places.toml_edit import loaded
from media_hygiene.review.home_paths import HOME_PATHS
from media_hygiene.review.http import Request
from media_hygiene.review.lan_paths import READ_PATHS
from media_hygiene.review.lan_switch_api import (
    LAN_SWITCH_PATH,
    lan_switch_route,
    switch_of,
)
from media_hygiene.review.write_routes import CHANGES

if TYPE_CHECKING:
    from pathlib import Path

_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}


def _ask(
    config_file: Path, method: str, body: object = None
) -> tuple[HTTPStatus, dict[str, object]]:
    """Send a request as the page does."""
    data = b"" if body is None else json.dumps(body).encode()
    request = Request(method, LAN_SWITCH_PATH, _JSON, data)
    reply = asyncio.run(lan_switch_route(config_file, request))
    return reply.status, json.loads(reply.body or b"{}")


def test_no_file_reads_the_defaults(tmp_path: Path) -> None:
    """Nothing written: the settings' own defaults."""
    status, answer = _ask(tmp_path / "config.toml", "GET")
    default = ReviewSettings()
    assert status == HTTPStatus.OK
    assert answer["lan"] == {
        "lan": default.lan,
        "originals": default.lan_phone_originals,
    }


def test_odd_values_read_as_defaults(tmp_path: Path) -> None:
    """A string or a broken file never reaches the page as a switch."""
    config = tmp_path / "config.toml"
    config.write_text("[review]\nlan = 'yes'\n", "utf-8")
    assert switch_of(config) == {"lan": True, "originals": False}
    config.write_text("[review\n", "utf-8")
    assert switch_of(config) == {"lan": True, "originals": False}


def test_a_change_is_written_read_back_and_said_later(tmp_path: Path) -> None:
    """Comments kept; the answer is the file's; it says when it applies."""
    config = tmp_path / "config.toml"
    config.write_text("# mine\n[review]\nport = 8088 # keep\n", "utf-8")
    status, answer = _ask(config, "POST", {"lan": False, "originals": True})
    assert status == HTTPStatus.OK
    assert answer["lan"] == {"lan": False, "originals": True}
    assert answer["later"]
    text = config.read_text("utf-8")
    assert "# mine" in text
    assert "# keep" in text
    table: dict[str, object] = dict(loaded(config)["review"])
    assert table["lan"] is False
    assert table["lan_phone_originals"] is True
    ReviewSettings.model_validate(table)


def test_bad_body_and_method_are_refused(tmp_path: Path) -> None:
    """A body missing a switch is 400, another method 405; the file is untouched."""
    config = tmp_path / "config.toml"
    assert _ask(config, "POST", {"lan": True})[0] == HTTPStatus.BAD_REQUEST
    assert _ask(config, "PUT", {})[0] == HTTPStatus.METHOD_NOT_ALLOWED
    assert not config.exists()


def test_the_route_is_the_pcs_alone() -> None:
    """Reachable by the home app, a write refused to a phone."""
    assert LAN_SWITCH_PATH in HOME_PATHS
    assert LAN_SWITCH_PATH in CHANGES
    assert LAN_SWITCH_PATH not in READ_PATHS
