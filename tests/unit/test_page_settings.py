"""Settings saved from the pages where they act (0606-0609)."""

from __future__ import annotations

import asyncio
import json
import tomllib
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.places.toml_edit import loaded
from media_hygiene.review import ai_state_api
from media_hygiene.review.ai_state_api import AI_STATE_PATH
from media_hygiene.review.http import Request
from media_hygiene.review.lan_paths import READ_PATHS
from media_hygiene.review.page_settings import SETTING_PATHS, setting_response
from media_hygiene.review.setting_groups import EVENTS_PATH, LOCALE_PATH, SLIDESHOW_PATH
from media_hygiene.review.write_routes import CHANGES

if TYPE_CHECKING:
    from pathlib import Path

_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}


def _send(config: Path, request: Request) -> tuple[HTTPStatus, dict[str, object]]:
    """Send a request as a page does."""
    reply = asyncio.run(setting_response(request, config))
    return reply.status, json.loads(reply.body or b"{}")


def _get(
    config: Path, path: str, method: str = "GET"
) -> tuple[HTTPStatus, dict[str, object]]:
    """A request without a body."""
    return _send(config, Request(method, path, _JSON, b""))


def _post(
    config: Path, path: str, body: object
) -> tuple[HTTPStatus, dict[str, object]]:
    """A `POST` with a JSON body."""
    return _send(config, Request("POST", path, _JSON, json.dumps(body).encode()))


def test_defaults_when_no_file(tmp_path: Path) -> None:
    """Nothing written: the settings' own defaults."""
    config = tmp_path / "config.toml"
    assert _get(config, LOCALE_PATH)[1]["values"] == {"locale": "en"}
    assert _get(config, SLIDESHOW_PATH)[1]["values"] == {"interval_seconds": 8}
    assert _get(config, EVENTS_PATH)[1]["values"] == {
        "merge_gap_hours": 18.0,
        "min_event_size": 5,
        "trip_min_km": 100.0,
    }


@pytest.mark.parametrize(
    "case",
    [
        (LOCALE_PATH, {"locale": "fr"}, "general"),
        (SLIDESHOW_PATH, {"interval_seconds": 12}, "slideshow"),
        (
            EVENTS_PATH,
            {"merge_gap_hours": 30, "min_event_size": 3, "trip_min_km": 60},
            "classify",
        ),
    ],
)
def test_a_change_is_written_and_read_back(
    tmp_path: Path, case: tuple[str, dict[str, object], str]
) -> None:
    """Comments kept; the answer is what the file holds."""
    path, body, table = case
    config = tmp_path / "config.toml"
    config.write_text("# mine\n[general]\ncolor = 'auto' # keep\n", "utf-8")
    status, answer = _post(config, path, body)
    assert status == HTTPStatus.OK
    assert answer["values"] == body
    assert answer["later"]
    text = config.read_text("utf-8")
    assert "# mine" in text
    assert "# keep" in text
    for key, value in body.items():
        assert dict(loaded(config)[table])[key] == value


@pytest.mark.parametrize(
    "case",
    [
        (LOCALE_PATH, {"locale": "de"}),
        (SLIDESHOW_PATH, {"interval_seconds": 1}),
        (SLIDESHOW_PATH, {"interval_seconds": True}),
        (SLIDESHOW_PATH, {"interval_seconds": 5, "extra": 1}),
        (EVENTS_PATH, {"merge_gap_hours": 1}),
    ],
)
def test_bad_values_are_refused_and_nothing_written(
    tmp_path: Path, case: tuple[str, dict[str, object]]
) -> None:
    """Out of bounds, a bool, an unknown or missing key: 400, file untouched."""
    path, body = case
    config = tmp_path / "config.toml"
    assert _post(config, path, body)[0] == HTTPStatus.BAD_REQUEST
    assert not config.exists()
    assert _get(config, path, "PUT")[0] == HTTPStatus.METHOD_NOT_ALLOWED


def test_odd_file_reads_as_defaults(tmp_path: Path) -> None:
    """A value out of bounds or a broken file never reaches the page."""
    config = tmp_path / "config.toml"
    config.write_text("[slideshow]\ninterval_seconds = 9999\n", "utf-8")
    assert _get(config, SLIDESHOW_PATH)[1]["values"] == {"interval_seconds": 8}
    config.write_text("[slideshow\n", "utf-8")
    assert _get(config, SLIDESHOW_PATH)[1]["values"] == {"interval_seconds": 8}


def test_ai_state_found_absent_and_model_saved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The listing comes from the url; the model is saved nested, then read back."""
    config = tmp_path / "config.toml"
    config.write_text("[classify.ai]\nurl = 'http://x:1'\n", "utf-8")
    monkeypatch.setattr(ai_state_api, "installed_models", lambda _url: ["b", "a"])
    state = _get(config, AI_STATE_PATH)[1]
    assert state["found"] is True
    assert state["models"] == ["b", "a"]
    assert state["model"] == ""
    saved = _post(config, AI_STATE_PATH, {"model": "a"})
    assert saved[0] == HTTPStatus.OK
    written = tomllib.loads(config.read_text("utf-8"))
    assert written["classify"]["ai"] == {"url": "http://x:1", "model": "a"}
    monkeypatch.setattr(ai_state_api, "installed_models", lambda _url: None)
    state = _get(config, AI_STATE_PATH)[1]
    assert (state["found"], state["model"], state["models"]) == (False, "a", [])


def test_installed_models_refuses_a_non_http_url() -> None:
    """Only http(s): never a file: URL."""
    assert ai_state_api.installed_models("file:///etc/passwd") is None


def test_routes_are_the_pcs_alone() -> None:
    """Writes refused to a phone: declared as changes, absent from its list."""
    for path in SETTING_PATHS:
        assert path in CHANGES
        assert path not in READ_PATHS
