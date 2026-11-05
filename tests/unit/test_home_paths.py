"""Every path `HomeApp` routes is routed to it by the home server (0584)."""

from __future__ import annotations

import inspect
import re

from media_hygiene.review import home_app
from media_hygiene.review.home_paths import HOME_PATHS

_COMPARED = re.compile(r"path == ([A-Z_]+_PATH)\b")


def test_every_path_home_app_answers_is_a_home_path() -> None:
    """A path `HomeApp` answers but the home server sends to `library` gets a 405."""
    source = inspect.getsource(home_app.HomeApp)
    names = set(_COMPARED.findall(source))
    assert names, "no path found: the pattern no longer matches HomeApp"
    missing = {name for name in names if getattr(home_app, name) not in HOME_PATHS}
    assert not missing


def test_favourites_scope_and_import_steps_reach_home_app() -> None:
    """The three settings the home page saves (the 405 of 2026-11-03)."""
    wanted = {"/api/favourites", "/api/scan-scope", "/api/import-steps"}
    assert wanted <= HOME_PATHS
