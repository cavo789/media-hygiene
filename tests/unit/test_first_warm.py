"""The warm-up of the first clicks after the home server listens (0677)."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.review.http import Request, Response
from media_hygiene.search.app import SEARCH_PAGE_PATH, SEARCH_PATH
from media_hygiene.services import first_warm
from media_hygiene.services.first_warm import WARM_PEOPLE, WARM_REQUESTS, warmed

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


async def _serve(handled: list[Request], fails: bool = False) -> list[int]:  # noqa: FBT001, FBT002
    """Start the warm-up as the server would and let it run.

    Args:
        handled: Receives each request the warm-up sent.
        fails: The router raises.

    Returns:
        The ports `ready` was told.
    """
    told: list[int] = []

    class Router:
        """Records what it is asked."""

        async def handle(self, request: Request) -> Response:
            """Record a request.

            Args:
                request: The request.

            Returns:
                200.

            Raises:
                RuntimeError: When asked to fail.
            """
            handled.append(request)
            if fails:
                raise RuntimeError
            return Response(HTTPStatus.OK)

    with ThreadPoolExecutor(1) as pool:
        warmed(told.append, Router(), pool)(1234)
        await asyncio.sleep(0.05)
    return told


def _idle(monkeypatch: pytest.MonkeyPatch, busy: bool = False) -> None:  # noqa: FBT001, FBT002
    """No delay; the index written by another connection, or not.

    Args:
        monkeypatch: The fixture.
        busy: An audit or `people` writes the index, or nobody is named.
    """
    monkeypatch.setattr(first_warm, "WARM_DELAY", 0.0)
    monkeypatch.setattr(first_warm, "people_worth_warming", lambda: not busy)


def test_ready_first_then_the_library_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    """The server's message goes first; the page and an empty search follow."""
    _idle(monkeypatch)
    handled: list[Request] = []
    assert asyncio.run(_serve(handled)) == [1234]
    assert [(each.method, each.path) for each in handled] == [
        ("GET", SEARCH_PAGE_PATH),
        ("POST", SEARCH_PATH),
        ("GET", "/api/folders"),  # the kept states built ahead (0804)
        ("GET", "/api/found-events"),
        ("GET", "/places/"),
        ("GET", "/people/"),  # last: its build writes its face groups (0817)
    ]
    assert handled == [*WARM_REQUESTS, WARM_PEOPLE]


def test_the_people_page_waits_for_a_writer(monkeypatch: pytest.MonkeyPatch) -> None:
    """An audit writing the index: the people page is left for the visit."""
    _idle(monkeypatch, busy=True)
    handled: list[Request] = []
    asyncio.run(_serve(handled))
    assert handled == list(WARM_REQUESTS)


def test_a_failure_leaves_no_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    """A router that raises stops the warm-up silently: the real request tells."""
    _idle(monkeypatch)
    handled: list[Request] = []
    asyncio.run(_serve(handled, fails=True))
    assert len(handled) == 1


def test_stopped_before_it_starts() -> None:
    """A server stopping during the delay cancels the warm-up: nothing is sent."""
    handled: list[Request] = []
    asyncio.run(_serve(handled))
    assert not handled


def _config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    """A config.toml and a writable index under `tmp_path`.

    Args:
        tmp_path: The test's folder.
        monkeypatch: The fixture.
        text: The configuration file's content.
    """
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "config.toml").write_text(text, encoding="utf-8")
    monkeypatch.setenv("MEDIA_HYGIENE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("MEDIA_HYGIENE_CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(first_warm, "index_busy", lambda _index: False)


def test_nobody_named_no_people_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Faces found but nobody named: the page waits for a visit (review 2026-11-13)."""
    _config(tmp_path, monkeypatch, "")
    assert not first_warm.people_worth_warming()


def test_someone_named_the_people_page_is_built(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A name given and the index free: the page is built ahead."""
    _config(tmp_path, monkeypatch, '[[people.person]]\nname = "Ann"\n')
    assert first_warm.people_worth_warming()


def test_unreadable_settings_no_people_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A broken config.toml: nothing built, the visit says what is wrong."""
    _config(tmp_path, monkeypatch, "[[people.person]\n")
    assert not first_warm.people_worth_warming()
