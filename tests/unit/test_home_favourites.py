"""The home page's favourites: `[home] favorites` written, read back, drawn (0484)."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_favourites import (
    SUGGESTED,
    read_favourites,
    save_favourites,
    shown_favourites,
)
from media_hygiene.cli.home_state import home_state
from media_hygiene.config.loader import load_settings
from media_hygiene.review.ending import Ending
from media_hygiene.review.home_app import FAVOURITES_PATH, HomeApp
from media_hygiene.review.home_favourites_api import favourites_response
from media_hygiene.review.http import Request
from media_hygiene.review.lan_paths import READ_PATHS
from media_hygiene.services.home import home_page
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}
_COMMENTED: Final = '# mine\n[general]\n# keep me\nlocale = "en"\n'


def _post(config_file: Path, names: object) -> tuple[HTTPStatus, dict[str, object]]:
    """Send the list as the page does."""
    body = json.dumps({"names": names}).encode()
    request = Request("POST", FAVOURITES_PATH, _JSON, body)
    reply = asyncio.run(favourites_response(config_file, request))
    return reply.status, json.loads(reply.body or b"{}")


def test_a_list_saved_is_read_back_and_the_comments_kept(tmp_path: Path) -> None:
    """Written with tomlkit: the user's comments stay; the answer is the file's."""
    config_file = tmp_path / "config.toml"
    config_file.write_text(_COMMENTED, encoding="utf-8")
    assert save_favourites(config_file, ["search", "import"]) == ("search", "import")
    text = config_file.read_text(encoding="utf-8")
    assert "# mine" in text
    assert "# keep me" in text
    assert read_favourites(config_file) == ("search", "import")


def test_the_order_is_kept_after_a_move(tmp_path: Path) -> None:
    """A card moved: the new order is the file's."""
    config_file = tmp_path / "config.toml"
    save_favourites(config_file, ["search", "import", "audit"])
    status, answer = _post(config_file, ["audit", "search", "import"])
    assert status is HTTPStatus.OK
    assert answer == {"favourites": ["audit", "search", "import"]}
    assert read_favourites(config_file) == ("audit", "search", "import")


def test_an_unknown_name_is_ignored_not_an_error(tmp_path: Path) -> None:
    """A verb renamed or removed: left out when drawn, the settings still load."""
    locations = make_locations(tmp_path)
    locations.config_file.write_text(
        '[home]\nfavorites = ["gone-verb", "search"]\n', encoding="utf-8"
    )
    assert load_settings(locations).settings.home.favorites == ("gone-verb", "search")
    state = home_state(make_runtime(locations))
    assert state.favourites == ("search",)
    assert not state.suggested
    assert not shown_favourites(("gone-verb",), {"search"})


def test_none_starred_suggests_three(tmp_path: Path) -> None:
    """No list: the library, an import, an audit, marked as suggested."""
    state = home_state(make_runtime(make_locations(tmp_path)))
    assert state.suggested
    assert state.favourites == SUGGESTED


def test_a_bad_body_is_refused_and_writes_nothing(tmp_path: Path) -> None:
    """Not a list of names: 400, no file written; odd names dropped."""
    config_file = tmp_path / "config.toml"
    assert _post(config_file, "search")[0] is HTTPStatus.BAD_REQUEST
    assert not config_file.exists()
    assert _post(config_file, ["Search!", "audit"])[1] == {"favourites": ["audit"]}


def test_the_home_app_routes_it_and_a_phone_cannot(tmp_path: Path) -> None:
    """The PC's page saves through `HomeApp`; the phone's list never names it."""
    runtime = make_runtime(make_locations(tmp_path))
    app = HomeApp(
        home_page(),
        lambda: home_state(runtime),
        runtime.locations.reports_dir,
        Ending(),
        audit=None,  # type: ignore[arg-type]  # never reached by this route
        presence=None,  # type: ignore[arg-type]
        config_file=runtime.locations.config_file,
    )
    body = json.dumps({"names": ["import"]}).encode()
    reply = asyncio.run(app.answer(Request("POST", FAVOURITES_PATH, _JSON, body)))
    assert reply.status is HTTPStatus.OK
    assert read_favourites(runtime.locations.config_file) == ("import",)
    assert FAVOURITES_PATH not in READ_PATHS
    phone = home_page(remote=True).decode()
    assert "const canStar = () => !REMOTE" in phone


def test_the_family_title_is_the_setting_else_our_photos(tmp_path: Path) -> None:
    """`[home] family_title` names the phone's page; empty by default (0461)."""
    locations = make_locations(tmp_path)
    assert not home_state(make_runtime(locations)).family_title
    locations.config_file.write_text(
        '[home]\nfamily_title = "Chez nous"\n', encoding="utf-8"
    )
    assert home_state(make_runtime(locations)).family_title == "Chez nous"
    phone = home_page(remote=True).decode()
    assert "S.family_title || T.familyTitle" in phone
