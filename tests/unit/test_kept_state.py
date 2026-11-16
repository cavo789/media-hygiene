"""The pages' kept states (0804): built again on every change, never otherwise."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.review.http import Request, Response
from media_hygiene.search.folders import FolderDesk
from media_hygiene.search.fts import SearchIndex
from media_hygiene.services import first_warm
from media_hygiene.services.kept_state import (
    KeptState,
    config_signature,
    connection_file,
    index_signature,
)
from media_hygiene.services.prefixed_page import KeptPage

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.ending import Handling
    from media_hygiene.search.chosen_api import ChosenDesk
    from media_hygiene.services.fresh_runtime import FreshRuntime

_ROOT = "/data/c/photos"


def _index(path: Path, *paths: str) -> Path:
    """Write a bare index of files.

    Args:
        path: The index file.
        paths: The files it lists.

    Returns:
        The file.
    """
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS files (path TEXT, size INT)")
        connection.executemany(
            "INSERT INTO files VALUES (?, 1)", [(each,) for each in paths]
        )
    connection.close()
    return path


def _counter(key: Callable[[], object]) -> tuple[KeptState[int], Callable[[], int]]:
    """A kept state whose value is how many builds it took.

    Args:
        key: The key it is kept under.

    Returns:
        The state, and the ask.
    """
    kept: KeptState[int] = KeptState()
    return kept, lambda: kept.value(key, lambda: kept.builds + 1)  # type: ignore[arg-type]


@pytest.fixture(name="index")
def index_fixture(tmp_path: Path) -> Path:
    """An index of one file."""
    return _index(tmp_path / "index.sqlite", f"{_ROOT}/a.jpg")


def _commit_elsewhere(index: Path) -> None:
    """Another connection adds a file (an audit, `sort`, `undo`).

    Args:
        index: The index.
    """
    _index(index, f"{_ROOT}/b.jpg")


def _move_by_sort(index: Path) -> None:
    """`sort` or `undo` moves a file: its row's path changes.

    Args:
        index: The index.
    """
    with sqlite3.connect(index) as connection:
        connection.execute("UPDATE files SET path = ?", (f"{_ROOT}/2024/a.jpg",))
    connection.close()


def _atomic_save(path: Path) -> None:
    """Replace a file by another one (a new inode): `shrink`, a restore, an editor.

    Args:
        path: The file.
    """
    other = path.with_name(path.name + ".new")
    shutil.copyfile(path, other)
    other.replace(path)


def _copy_keeping_mtime(path: Path) -> None:
    """Copy another file over it, its modification time kept.

    Args:
        path: The file.
    """
    other = path.with_name(path.name + ".old")
    shutil.copy2(path, other)
    os.utime(other, ns=(1, 1))
    shutil.copy2(other, path)


def _touch(path: Path) -> None:
    """`touch` it.

    Args:
        path: The file.
    """
    path.touch()


def _in_place(path: Path) -> None:
    """Edit it in place, its size and inode kept.

    Args:
        path: The file.
    """
    with path.open("r+b") as stream:
        stream.seek(100)
        stream.write(b"\0")


def _other_process(index: Path) -> None:
    """Another process commits into the index (an audit running in its container).

    Args:
        index: The index.
    """
    script = (
        "import sqlite3, sys; c = sqlite3.connect(sys.argv[1]);"
        " c.execute(\"INSERT INTO files VALUES ('/data/c/photos/z.jpg', 1)\");"
        " c.commit(); c.close()"
    )
    subprocess.run([sys.executable, "-c", script, str(index)], check=True)  # noqa: S603


@pytest.mark.parametrize(
    "event",
    [
        _commit_elsewhere,
        _move_by_sort,
        _atomic_save,
        _copy_keeping_mtime,
        _touch,
        _in_place,
        _other_process,
    ],
)
def test_every_index_event_builds_again(
    index: Path, event: Callable[[Path], None]
) -> None:
    """A commit, a move by `sort`/`undo`, a file replaced, copied, touched."""
    _, ask = _counter(lambda: index_signature(index))
    assert ask() == ask() == 1
    event(index)
    assert ask() == 2
    assert ask() == 2


def test_a_wal_file_counts(index: Path) -> None:
    """A writer in WAL mode commits into `-wal`: the key sees it."""
    _, ask = _counter(lambda: index_signature(index))
    assert ask() == 1
    index.with_name(index.name + "-wal").write_bytes(b"x")
    assert ask() == 2


def test_a_file_renamed_by_the_user_waits_for_the_index(
    index: Path, tmp_path: Path
) -> None:
    """A photo renamed in Explorer: the pages read the index, the next audit tells."""
    photo = tmp_path / "a.jpg"
    photo.write_bytes(b"x")
    _, ask = _counter(lambda: index_signature(index))
    assert ask() == 1
    photo.rename(tmp_path / "b.jpg")
    assert ask() == 1
    _commit_elsewhere(index)  # the audit forgets it, lists the new name
    assert ask() == 2


def _new_file(path: Path) -> None:
    """A file added in a new folder (an event remembered).

    Args:
        path: The file.
    """
    path.parent.mkdir()
    path.touch()


@pytest.fixture(name="config")
def config_fixture(tmp_path: Path) -> Path:
    """`/config` with `config.toml` and a person's file."""
    config = tmp_path / "config"
    (config / "people").mkdir(parents=True)
    (config / "config.toml").write_text("[people]\n", encoding="utf-8")
    (config / "people" / "ann.toml").write_text("faces = []\n", encoding="utf-8")
    return config


@pytest.mark.parametrize(
    "event",
    [
        lambda config: _in_place(config / "config.toml"),
        lambda config: (config / "config.toml").write_text("[x]\n", encoding="utf-8"),
        lambda config: _atomic_save(config / "people" / "ann.toml"),
        lambda config: _copy_keeping_mtime(config / "config.toml"),
        lambda config: _touch(config / "people" / "ann.toml"),
        lambda config: _new_file(config / "events" / "y"),
        lambda config: (config / "people" / "ann.toml").unlink(),
    ],
)
def test_every_config_event_builds_again(
    config: Path, event: Callable[[Path], None]
) -> None:
    """An edit, an atomic save, a copy, a touch, a file added or removed."""
    (config / "config.toml").write_text("[people]\n" + " " * 200, encoding="utf-8")
    _, ask = _counter(lambda: config_signature(config))
    assert ask() == 1
    event(config)
    assert ask() == 2


def test_the_history_folder_is_left_out(config: Path) -> None:
    """A previous version kept by a save is no change of its own."""
    _, ask = _counter(lambda: config_signature(config))
    assert ask() == 1
    (config / ".history").mkdir()
    _touch(config / ".history" / "config.toml")
    assert ask() == 1


def test_a_failed_build_keeps_nothing(index: Path) -> None:
    """The next ask builds again after an exception."""
    kept: KeptState[int] = KeptState()

    def fails() -> int:
        message = "broken"
        raise ValueError(message)

    with pytest.raises(ValueError, match="broken"):
        kept.value(lambda: index_signature(index), fails)
    assert kept.value(lambda: index_signature(index), lambda: 7) == 7
    kept.forget()
    assert kept.value(lambda: index_signature(index), lambda: 8) == 8


def test_an_index_in_memory_is_never_kept() -> None:
    """No file to watch: built at every ask."""
    connection = sqlite3.connect(":memory:")
    assert connection_file(connection) is None
    _, ask = _counter(lambda: index_signature(None))
    assert ask() == 1
    assert ask() == 2
    connection.close()


def test_the_folder_tree_follows_the_index(index: Path) -> None:
    """`GET /api/folders` kept, then a folder added by an audit shows."""
    with SearchIndex.open(index) as search:
        desk = FolderDesk(
            search,
            HostPathMapper(Path("/data")),
            (Path(_ROOT),),
            cast("ChosenDesk", None),
        )
        first = json.loads(desk.tree().body)
        assert json.loads(desk.tree().body) == first
        assert desk.kept.builds == 1
        _index(index, f"{_ROOT}/2024/c.jpg")
        inside = [row["inside"] for row in json.loads(desk.tree().body)["folders"]]
        assert f"{_ROOT}/2024" in inside
        assert desk.kept.builds == 2


def test_the_people_page_keeps_its_app_until_a_name_is_saved(
    index: Path, config: Path
) -> None:
    """Same app (its session, *Apply now*, files set aside) while nothing changed."""
    locations = SimpleNamespace(index_file=index, config_dir=config)
    runtime = SimpleNamespace(locations=locations, settings="settings")
    fresh = SimpleNamespace(runtime=lambda: runtime)
    built: list[object] = []

    def build(_: object) -> Handling:
        built.append(object())
        return cast("Handling", _Answer())

    page = KeptPage("/people/", cast("FreshRuntime", fresh), build)
    asked = Request("GET", "/people/", {"host": "127.0.0.1"})
    asyncio.run(page.handle(asked))
    asyncio.run(page.handle(asked))
    assert len(built) == 1
    (config / "people" / "ann.toml").write_text("faces = [1]\n", encoding="utf-8")
    asyncio.run(page.handle(asked))  # the name saved by the page itself
    assert len(built) == 2


def test_a_failed_warm_up_leaves_the_visit_working(
    index: Path, config: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The warm-up's build fails (0817): no trace, nothing kept, the visit builds."""
    locations = SimpleNamespace(index_file=index, config_dir=config)
    runtime = SimpleNamespace(locations=locations, settings="settings")
    fresh = SimpleNamespace(runtime=lambda: runtime)
    built: list[object] = []

    def build(_: object) -> Handling:
        built.append(object())
        if len(built) == 1:
            locked = "database is locked"
            raise sqlite3.OperationalError(locked)
        return cast("Handling", _Answer())

    page = KeptPage("/people/", cast("FreshRuntime", fresh), build)

    class Router:
        """The people page under its prefix, 200 for the rest."""

        async def handle(self, request: Request) -> Response:
            """Answer.

            Args:
                request: The request.

            Returns:
                The page's answer, or 200.
            """
            if page.serves(request.path):
                return await page.handle(request)
            return Response(HTTPStatus.OK)

    monkeypatch.setattr(first_warm, "WARM_DELAY", 0.0)
    monkeypatch.setattr(first_warm, "_index_busy", lambda: False)
    with ThreadPoolExecutor(1) as pool:
        asyncio.run(first_warm.warm_first_clicks(Router(), pool))
    assert len(built) == 1
    asked = Request("GET", "/people/", {"host": "127.0.0.1"})
    assert asyncio.run(page.handle(asked)).status == HTTPStatus.OK
    assert len(built) == 2


class _Answer:
    """An app answering 200."""

    async def handle(self, request: Request) -> Response:
        """Answer.

        Args:
            request: The request.

        Returns:
            200.
        """
        del request
        return Response(HTTPStatus.OK)
