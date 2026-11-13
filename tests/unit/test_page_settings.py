"""Settings saved from the pages where they act (0606-0609)."""

from __future__ import annotations

import asyncio
import json
import tomllib
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from unittest.mock import MagicMock

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import _, active_locale, install
from media_hygiene.i18n.live import PerLocale, page_of
from media_hygiene.places.toml_edit import loaded
from media_hygiene.review import ai_state_api
from media_hygiene.review.ai_state_api import AI_STATE_PATH
from media_hygiene.review.http import Request
from media_hygiene.review.lan_paths import READ_PATHS
from media_hygiene.review.local_app import PAGE_PATH, page_or_state
from media_hygiene.review.page_settings import SETTING_PATHS, setting_response
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.review.setting_groups import (
    EVENTS_PATH,
    LOCALE_PATH,
    SHARE_PATH,
    SLIDESHOW_PATH,
)
from media_hygiene.review.write_routes import CHANGES
from media_hygiene.services.home import home_page
from media_hygiene.services.phone_review import phone_page
from media_hygiene.services.review_file import review_page
from media_hygiene.services.slideshow_build import show_app
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

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
        (SHARE_PATH, {"long_side_px": 1600, "quality": 80, "keep_gps": True}, "share"),
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
        (SHARE_PATH, {"long_side_px": 2048, "quality": 85, "keep_gps": 1}),
        (SHARE_PATH, {"long_side_px": 100, "quality": 85, "keep_gps": False}),
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


def test_the_language_applies_at_once(tmp_path: Path) -> None:
    """0644: saved, the server speaks it and the page is told to reload."""
    config = tmp_path / "config.toml"
    status, answer = _post(config, LOCALE_PATH, {"locale": "fr"})
    assert status == HTTPStatus.OK
    assert answer["reload"] is True
    assert active_locale() is Locale.FR
    assert str(answer["later"]).startswith("Appliqu")  # said in French
    _status, other = _post(config, SLIDESHOW_PATH, {"interval_seconds": 9})
    assert "reload" not in other


def test_a_page_drawn_per_language_follows_it() -> None:
    """0644: the page is drawn again in the new language, once per language."""
    drawn: list[Locale] = []

    def draw() -> bytes:
        drawn.append(active_locale())
        return _("Language").encode()

    page = PerLocale(draw)
    english = page()
    install(Locale.FR)
    assert page() != english
    assert page() == page()
    assert drawn == [Locale.EN, Locale.FR]
    assert page_of(b"x") == b"x"
    assert page_of(page) == page()


def test_the_ai_card_is_one_shared_template() -> None:
    """0645: the home page draws the 🤖 card from `ai_card.html.j2`."""
    page = home_page().decode()
    assert "window.mhAiCard = " in page
    assert "window.mhAiCard(box)" in page
    assert AI_STATE_PATH in page


def _follows(draw: Callable[[], bytes], french: str) -> None:
    """0647: drawn in English, then, the language changed, in French: same object."""
    page = PerLocale(draw)
    assert french not in page().decode()
    install(Locale.FR)
    assert french in page().decode()


_LANGUAGE_FR: Final = "Langue"  # in the bar of every page


def test_the_review_page_follows_the_language() -> None:
    """0647: a review page reloaded after a change is in the new language."""
    place = DecisionsPlace("decisions.json", "C:\\decisions.json")
    _follows(partial(review_page, "review.html.j2", place, ("/d", "/f")), _LANGUAGE_FR)


def test_the_phone_page_follows_the_language() -> None:
    """0647: the page freeing a phone, drawn per language, reloads in the new one."""
    place = DecisionsPlace("decisions.json", "C:\\decisions.json")
    page = phone_page(place)
    english = page()
    install(Locale.FR)
    assert page() != english
    assert _LANGUAGE_FR.encode() in page()


def test_the_home_page_of_a_phone_follows_the_language() -> None:
    """0647: the home page drawn for a phone (`mh --lan`)."""
    page = PerLocale(lambda: home_page(remote=True))
    english = page()
    install(Locale.FR)
    assert page() != english


def test_the_slideshow_follows_the_language(locations: Locations) -> None:
    """0647: the remote and the TV's screen of a show."""
    app = show_app(make_runtime(locations), MagicMock(), MagicMock())
    remote, screen = page_of(app.pages.remote), page_of(app.pages.screen)
    install(Locale.FR)
    assert page_of(app.pages.remote) != remote
    assert page_of(app.pages.screen) != screen


def test_a_served_page_uses_the_language_of_the_moment() -> None:
    """0647: `page_or_state` draws at each load, whichever the server holds."""
    page = PerLocale(lambda: _("Language").encode())
    english = page_or_state(PAGE_PATH, page, MagicMock())
    install(Locale.FR)
    assert page_or_state(PAGE_PATH, page, MagicMock()).body != english.body


def test_no_page_is_said_to_keep_its_language(tmp_path: Path) -> None:
    """0647: the sentence of exceptions is gone from what the save says."""
    _status, answer = _post(tmp_path / "config.toml", LOCALE_PATH, {"locale": "en"})
    assert "mh starts again" not in str(answer["later"])


def test_share_defaults_and_switch_read_back(tmp_path: Path) -> None:
    """0747: the copies to send, from the album bar; a bad value: the default."""
    config = tmp_path / "config.toml"
    assert _get(config, SHARE_PATH)[1]["values"] == {
        "long_side_px": 2048,
        "quality": 85,
        "keep_gps": False,
    }
    config.write_text("[share]\nkeep_gps = 'yes'\nquality = 70\n", "utf-8")
    values = _get(config, SHARE_PATH)[1]["values"]
    assert values == {"long_side_px": 2048, "quality": 70, "keep_gps": False}
