"""`slideshow` from the command line to its server (0291), and what its window says.

The command refuses a missing choice and an empty selection; served, it answers the
remote and the screen on the loopback until the page's stop; the window says how the
TV and the phone open it, or how to open it to them (`mh slideshow --lan`).
"""

from __future__ import annotations

import json
import queue
import sqlite3
import threading
import urllib.request
from contextlib import closing
from typing import TYPE_CHECKING, Final

import pytest
from PIL import Image
from typer.testing import CliRunner

from media_hygiene.constants import ExitCode
from media_hygiene.errors import MediaHygieneError
from media_hygiene.index.schema import prepare
from media_hygiene.review.lan import LanAccess
from media_hygiene.services import slideshow
from media_hygiene.services.slideshow import ShowStart, serve_slideshow
from media_hygiene.services.slideshow_pick import Pick
from media_hygiene.services.slideshow_say import say_slideshow
from tests.support.cli import point_mounts, run
from tests.support.runtime import make_locations, make_runtime, output_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_FOLDER: Final = r"C:\Photos\Holidays"
_TIMEOUT: Final = 10.0


def _library(locations: Locations) -> None:
    """Two photos in the Holidays folder of drive C, known to the index."""
    folder = locations.data_dir / "c" / "Photos" / "Holidays"
    folder.mkdir(parents=True)
    with closing(sqlite3.connect(locations.index_file)) as connection:
        prepare(connection)
        for number in range(2):
            photo = folder / f"IMG_{number}.jpg"
            Image.new("RGB", (64, 48)).save(photo)
            connection.execute(
                "INSERT INTO files (path, size, mtime_ns) VALUES (?, ?, 1)",
                (str(photo), photo.stat().st_size),
            )
        connection.commit()


def test_the_command_asks_what_to_show(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without --folder, --search nor --chosen: the three forms, a failure code."""
    locations = make_locations(tmp_path)
    _library(locations)
    point_mounts(locations, monkeypatch)
    result = run(CliRunner(), "slideshow")
    assert result.exit_code == ExitCode.FAILURE
    assert "--chosen" in result.output


def test_an_empty_selection_is_said(tmp_path: Path) -> None:
    """A folder the last audit did not see: nothing to show, said with a tip."""
    runtime = make_runtime(make_locations(tmp_path))
    _library(runtime.locations)
    with pytest.raises(MediaHygieneError, match="No photo or video to show"):
        serve_slideshow(runtime, ShowStart(Pick(folder=r"C:\Elsewhere"), 0))


def _get(port: int, path: str) -> bytes:
    with urllib.request.urlopen(
        f"http://127.0.0.1:{port}{path}", timeout=_TIMEOUT
    ) as answer:
        return bytes(answer.read())


def _stop(port: int) -> None:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/stop",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=_TIMEOUT) as answer:  # noqa: S310
        answer.read()


def test_the_show_is_served_until_the_page_stops_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The remote, the screen, the photos, the show; the stop ends the command."""
    runtime = make_runtime(make_locations(tmp_path))
    _library(runtime.locations)
    ports: queue.Queue[int] = queue.Queue()
    monkeypatch.setattr(slideshow, "address_tip", lambda _output, port: ports.put(port))
    shown: queue.Queue[int] = queue.Queue()
    start = ShowStart(Pick(folder=_FOLDER), 0)
    thread = threading.Thread(target=lambda: shown.put(serve_slideshow(runtime, start)))
    thread.start()
    port = ports.get(timeout=_TIMEOUT)
    try:
        assert b"slideshow.js" not in _get(port, "/")  # the script is inline
        assert b"XMLHttpRequest" in _get(port, "/screen")
        slides = json.loads(_get(port, "/api/slides"))["slides"]
        assert len(slides) == 2
        tv = _get(port, f"/tv/{slides[0]['key']}.jpg")
        assert tv.startswith(b"\xff\xd8")
        state = json.loads(_get(port, "/api/show/0"))
        assert state["total"] == 2
    finally:
        _stop(port)
        thread.join(_TIMEOUT)
    assert shown.get(timeout=_TIMEOUT) == 2
    said = output_of(runtime)
    assert "Slideshow ready" in said
    assert "mh slideshow --lan" in said


def test_the_window_says_how_the_tv_and_the_phone_open_it(runtime_lan: Runtime) -> None:
    """Under mh --lan: the TV's address to bookmark, the phone's address and code."""
    access = LanAccess("192.168.1.20", 8088, b"ef" * 32)
    say_slideshow(runtime_lan.output, access)
    said = " ".join(output_of(runtime_lan).split())
    assert "http://192.168.1.20:8088/screen" in said
    assert access.shown_code in said


def test_an_address_refused_is_said(
    runtime_lan: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A public address given by mh: the slideshow stays on this PC, said."""
    monkeypatch.setenv("MEDIA_HYGIENE_LAUNCHER_LAN_ADDRESS", "8.8.8.8")
    say_slideshow(runtime_lan.output, None)
    assert "8.8.8.8 is not an address of a home network" in " ".join(
        output_of(runtime_lan).split()
    )


@pytest.fixture
def runtime_lan(tmp_path: Path) -> Runtime:
    """A runtime writing to memory."""
    return make_runtime(make_locations(tmp_path))
