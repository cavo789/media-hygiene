"""The chain after an import: its file, its route, after a page's copy (0604, 0619)."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.config.import_settings import ImportStep
from media_hygiene.review.http import Request
from media_hygiene.review.import_chain_api import (
    IMPORT_CHAIN_PATH,
    ChainDoor,
    import_chain_route,
)
from media_hygiene.review.step_watch import WATCH
from media_hygiene.services.import_chain import (
    CHAIN_FILE,
    ChainState,
    ImportChain,
    read_chain,
    waiting_chain,
)
from media_hygiene.services.import_chain_start import start_chain
from media_hygiene.services.import_end import imported
from media_hygiene.services.next_command import (
    LAUNCHER_STEPS_VARIABLE,
    LAUNCHER_VARIABLE,
)
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Response
    from media_hygiene.services.runtime import Runtime

_HEADERS: Final = {"host": "127.0.0.1:8080", "content-type": "application/json"}
_NOW: Final = datetime(2026, 11, 6, 12, tzinfo=UTC)


def _chain(state: ChainState, updated: datetime = _NOW) -> ImportChain:
    """A chain stopped or running at its bursts step.

    Args:
        state: Its state.
        updated: When its file was written.

    Returns:
        The chain.
    """
    return ImportChain(
        steps=(ImportStep.AUDIT, ImportStep.BURSTS, ImportStep.TAGS),
        at=ImportStep.BURSTS,
        state=state,
        folder=r"C:\Photos\Phone",
        since="today",
        updated=updated.isoformat(),
    )


def _write(tmp_path: Path, chain: ImportChain, *, mark: bool = False) -> Path:
    """Write a chain's file, as `mh.ps1` does when `mark` (a byte order mark).

    Args:
        tmp_path: The folder.
        chain: The chain.
        mark: With a byte order mark.

    Returns:
        The file.
    """
    file = tmp_path / CHAIN_FILE
    file.write_text(chain.model_dump_json(), "utf-8-sig" if mark else "utf-8")
    return file


def _ask(door: ChainDoor, method: str, body: bytes = b"") -> Response:
    """Answer one request.

    Args:
        door: The route's door.
        method: `GET` or `POST`.
        body: The body.

    Returns:
        The response.
    """
    request = Request(method, IMPORT_CHAIN_PATH, _HEADERS, body)
    return asyncio.run(import_chain_route(door, request))


def _runtime(tmp_path: Path) -> Runtime:
    """A runtime of real folders.

    Args:
        tmp_path: The test's folder.

    Returns:
        It.
    """
    locations = make_locations(tmp_path)
    for folder in (locations.cache_dir, locations.reports_dir):
        folder.mkdir(parents=True, exist_ok=True)
    return make_runtime(locations)


def test_powershell_file_is_read_and_damage_is_nothing(tmp_path: Path) -> None:
    """A byte order mark is read; a missing or damaged file is no chain."""
    file = _write(tmp_path, _chain(ChainState.STOPPED), mark=True)
    found = read_chain(file)
    assert found is not None
    assert found.at is ImportStep.BURSTS
    file.write_text("{not json", "utf-8")
    assert read_chain(file) is None
    file.unlink()
    assert read_chain(file) is None


def test_a_window_closed_is_said_stopped_once_stale(tmp_path: Path) -> None:
    """Running, recent: running. Its file too old: stopped, offered again."""
    file = _write(tmp_path, _chain(ChainState.RUNNING))
    recent = read_chain(file, _NOW + timedelta(hours=1))
    late = read_chain(file, _NOW + timedelta(hours=25))
    assert recent is not None
    assert recent.state is ChainState.RUNNING
    assert late is not None
    assert late.state is ChainState.STOPPED


def test_get_says_the_chain_and_the_line_to_type(tmp_path: Path) -> None:
    """The file as read, and the command from its step."""
    _write(tmp_path, _chain(ChainState.STOPPED))
    answer = _ask(ChainDoor(tmp_path / CHAIN_FILE, tmp_path, runs=False), "GET")
    said = json.loads(answer.body)
    assert said["chain"]["at"] == "bursts"
    assert said["command"] == "mh import --chain --from-step bursts"
    assert said["runs"] is False


def test_post_hands_the_step_to_mh(tmp_path: Path) -> None:
    """The words go where `mh` reads them, and the state says it waits."""
    _write(tmp_path, _chain(ChainState.STOPPED))
    door = ChainDoor(tmp_path / CHAIN_FILE, tmp_path, runs=True)
    answer = _ask(door, "POST", b'{"from": "tags"}')
    assert answer.status == HTTPStatus.OK
    written = json.loads((tmp_path / WATCH.now).read_text("utf-8"))
    assert written["words"] == ["import", "--chain", "--from-step", "tags"]


@pytest.mark.parametrize(
    "case",
    [
        (ChainState.RUNNING, True, b'{"from": "tags"}', HTTPStatus.CONFLICT),
        (ChainState.STOPPED, False, b'{"from": "tags"}', HTTPStatus.CONFLICT),
        (ChainState.STOPPED, True, b'{"from": "places"}', HTTPStatus.CONFLICT),
        (ChainState.STOPPED, True, b'{"from": "nope"}', HTTPStatus.BAD_REQUEST),
    ],
)
def test_post_refused(
    tmp_path: Path, case: tuple[ChainState, bool, bytes, HTTPStatus]
) -> None:
    """Running, no `mh` beside, a step out of the chain, a bad body: nothing handed."""
    state, runs, body, status = case
    _write(tmp_path, _chain(state))
    door = ChainDoor(tmp_path / CHAIN_FILE, tmp_path, runs=runs)
    assert _ask(door, "POST", body).status == status
    assert not (tmp_path / WATCH.now).exists()


def test_the_page_copy_leaves_the_console_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0619: the steps of `[imports] then`; the period finds what was copied."""
    monkeypatch.setenv(LAUNCHER_VARIABLE, "powershell")
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, WATCH.kept)
    runtime = _runtime(tmp_path)
    folder = tmp_path / "data" / "c" / "From NAS"
    (folder / "2019").mkdir(parents=True)
    older = folder / "IMG_20100101_000000.jpg"
    older.write_bytes(b"an earlier import")
    copied = (
        folder / "2019" / "IMG_20190503_101010.jpg",
        folder / "IMG_20200101_101010.jpg",
    )
    for path in copied:
        path.write_bytes(b"x")
    chain = start_chain(runtime, copied)
    assert chain is not None
    assert chain.steps == runtime.settings.imports.then
    assert chain.state is ChainState.WAITING
    assert chain.since == "2019-05-03"
    read = read_chain(runtime.locations.cache_dir / CHAIN_FILE)
    assert read == chain
    words = json.loads((runtime.locations.reports_dir / WATCH.now).read_text("utf-8"))
    assert words["words"] == ["import", "--chain"]
    found = imported(runtime, chain.folder, chain.since)
    assert set(copied) <= set(found)
    assert older not in found


def test_no_chain_without_step_copy_or_powershell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing copied or the bash `mh`: no file; the page says to audit again."""
    runtime = _runtime(tmp_path)
    monkeypatch.setenv(LAUNCHER_VARIABLE, "powershell")
    assert waiting_chain(runtime, ()) is None
    monkeypatch.setenv(LAUNCHER_VARIABLE, "bash")
    copy = tmp_path / "a.jpg"
    copy.write_bytes(b"x")
    assert waiting_chain(runtime, (copy,)) is None
    assert not (runtime.locations.cache_dir / CHAIN_FILE).exists()
