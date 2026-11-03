"""0567: the read-only steps chosen on the home page answer in the page."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.cli.page_capture import captured_step
from media_hygiene.cli.safety import PAGE_CAPTURED
from media_hygiene.review.http import Request
from media_hygiene.review.step_watch import served_here
from media_hygiene.services.console_here import (
    ReadOnlyHere,
    console_page,
    console_page_path,
)
from media_hygiene.services.fresh_runtime import FreshRuntime
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

_LOCAL: Final = {"host": "127.0.0.1"}


@pytest.mark.parametrize("name", sorted(PAGE_CAPTURED))
def test_each_step_is_a_page_of_the_home_server(name: str) -> None:
    """A click on the step is a plain link to its page."""
    assert served_here((name,)) == console_page_path(name)


def test_status_page_shows_what_the_console_prints(tmp_path: Path) -> None:
    """The page holds the same lines as the recorded command, no traceback."""
    runtime = make_runtime(make_locations(tmp_path))
    text = captured_step(runtime, "status")
    assert text.strip()
    page = console_page(runtime, "status").decode()
    first = next(line for line in text.splitlines() if line.strip() and "─" not in line)
    assert first.strip().split()[0] in page
    assert "Traceback" not in page


def test_config_page_names_the_settings(tmp_path: Path) -> None:
    """`config` lists its settings in the page."""
    text = captured_step(make_runtime(make_locations(tmp_path)), "config")
    assert "[general]" in text or "general" in text


def test_routes(tmp_path: Path) -> None:
    """The page, its slash, an unknown step and a write refused."""
    here = ReadOnlyHere(FreshRuntime(make_runtime(make_locations(tmp_path))))
    assert here.serves("/console/status/")
    assert here.serves("/history/")
    assert not here.serves("/search")

    def answer(method: str, path: str) -> HTTPStatus:
        return asyncio.run(here.handle(Request(method, path, _LOCAL))).status

    assert answer("GET", "/console/status/") == HTTPStatus.OK
    assert answer("GET", "/console/status") == HTTPStatus.SEE_OTHER
    assert answer("GET", "/console/clean/") == HTTPStatus.NOT_FOUND
    assert answer("POST", "/console/status/") == HTTPStatus.METHOD_NOT_ALLOWED
    assert answer("GET", "/history/") == HTTPStatus.OK


def test_an_unknown_step_is_refused(tmp_path: Path) -> None:
    """Only the read-only steps run for a page."""
    with pytest.raises(KeyError):
        captured_step(make_runtime(make_locations(tmp_path)), "clean")


@pytest.mark.parametrize("name", sorted(PAGE_CAPTURED))
def test_every_step_answers_without_a_traceback(tmp_path: Path, name: str) -> None:
    """Even without an index or reports, the page says what the console says."""
    page = console_page(make_runtime(make_locations(tmp_path)), name).decode()
    assert "<pre>" in page
    assert "Traceback" not in page
