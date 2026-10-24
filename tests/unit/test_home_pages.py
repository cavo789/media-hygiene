"""0356, 0358: the search app of the home server, built once, again on new settings."""

from __future__ import annotations

import contextlib
from functools import partial
from typing import TYPE_CHECKING, cast

from media_hygiene.errors import MountError
from media_hygiene.review.ending import Ending
from media_hygiene.services import home_pages
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_pages import HomeServer, SearchHere
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from collections.abc import Iterator
    from concurrent.futures import Executor
    from pathlib import Path

    import pytest

    from media_hygiene.search.app import SearchApp
    from media_hygiene.services.runtime import Runtime


_NO_INDEX = "No index yet."


def _here(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, index: list[bool]
) -> tuple[SearchHere, list[int]]:
    """The search of a home server; `index[0]`: whether the cache holds an index."""
    builds: list[int] = []

    @contextlib.contextmanager
    def opened(runtime: Runtime, *, words: bool) -> Iterator[object]:
        assert not words
        if not index[0]:
            raise MountError(_NO_INDEX)
        yield runtime

    def built(runtime: Runtime, _search: object, _build: object) -> SearchApp:
        builds.append(runtime.settings.review.port)
        return cast("SearchApp", object())

    monkeypatch.setattr(home_pages, "FreshRuntime", partial(FreshRuntime, every=0))
    monkeypatch.setattr(home_pages, "open_search", opened)
    monkeypatch.setattr(home_pages, "search_app", built)
    locations = make_locations(tmp_path)
    locations.config_dir.mkdir(parents=True, exist_ok=True)
    locations.config_file.write_text("[review]\nport = 8111\n", "utf-8")
    server = HomeServer(None, Ending(), cast("Executor", None))
    return SearchHere(make_runtime(locations), server), builds


def test_built_once_then_again_on_new_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same app while nothing changed; built again once `config.toml` changed."""
    here, builds = _here(tmp_path, monkeypatch, index=[True])
    first = here.app()
    assert here.app() is first
    assert builds == [8111]
    config = make_locations(tmp_path).config_file
    config.write_text("[review]\nport = 8112\n", "utf-8")
    assert here.app() is not None
    assert builds == [8111, 8112]
    here.close()


def test_no_index_yet_is_tried_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No index: the home page answers; once an audit made one, the search is there."""
    index = [False]
    here, builds = _here(tmp_path, monkeypatch, index=index)
    assert here.app() is None
    index[0] = True
    assert here.app() is not None
    assert builds == [8111]
