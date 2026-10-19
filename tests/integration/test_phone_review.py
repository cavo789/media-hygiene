"""The page freeing a phone (0248): its groups, its ticks read back, its end.

Real files and a real server: the three groups and their defaults (a set-aside never
ticked), every tick saved then read back from the disk, a forged choice refused, the
preview of the PC's file, and "Delete from the phone" giving `mh` the files ticked as
the file on the disk holds them — nothing when the page is left.
"""

from __future__ import annotations

import asyncio
import json
import queue
import threading
from typing import TYPE_CHECKING, Final

from typer.testing import CliRunner

from media_hygiene.cli.app import build_app
from media_hygiene.review.phone_app import PhoneApp
from media_hygiene.review.phone_file import PHONE_DECISIONS, read_phone_decisions
from media_hygiene.review.phone_session import PhonePages, PhoneSession
from media_hygiene.review.phone_views import TileSource
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.services import phone_review
from media_hygiene.services.phone_free import read_ticked
from media_hygiene.services.phone_plan import PHONE_REVIEW, PhoneCase
from media_hygiene.services.phone_review import PhoneReview, serve_phone_review
from tests.support.cli import point_mounts
from tests.support.review import JSON_HEADERS, PAGE, Call, send_call, serve_app_and_call
from tests.support.runtime import make_runtime
from tests.support.scenes import Shot, write_shot

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from media_hygiene.paths.locations import Locations

_DATE: Final = "2025-05-12T17:53:43Z"
_PHONE: Final = "Galaxy A72"
_LIBRARY: Final = "C:\\Photos\\2025\\IMG_1.jpg"


def _line(case: PhoneCase, path: str, *reason: str) -> str:
    """A plan line, as `phone-plan` writes it."""
    return "\t".join((case.value, path, "100", _DATE, *reason))


_PLAN: Final = (
    _line(PhoneCase.LIBRARY, "Camera/IMG_1.jpg", _LIBRARY),
    _line(PhoneCase.NEW, "Camera/IMG_new.jpg"),  # not imported: never shown
    _line(PhoneCase.DESTINATION, "Camera/IMG_2.jpg", "Camera/IMG_2.jpg"),
    _line(
        PhoneCase.SET_ASIDE,
        "Camera/burst.jpg",
        "20260101-120000",
        "purged",
        "2026-01-01T12:00:00+00:00",
        "quarantine-burst",
    ),
)


def _session(locations: Locations) -> PhoneSession:
    """The page on the plan above, its decisions file in /reports."""
    write_shot(locations.data_dir / "c/Photos/2025/IMG_1.jpg", Shot(7))
    locations.reports_dir.mkdir(parents=True, exist_ok=True)
    runtime = make_runtime(locations)
    files, _skipped = read_ticked(_PLAN)
    target = locations.reports_dir / PHONE_DECISIONS
    place = DecisionsPlace(PHONE_DECISIONS, PHONE_DECISIONS)
    tiles = TileSource(runtime.mapper, locations.data_dir / "c/Photos/Phone/A72")
    session = PhoneSession(PhonePages(_PHONE, files, tiles, (target, place)))
    session.save()
    return session


def _tick(*choices: tuple[int, bool]) -> Call:
    """`POST /api/phone`, as the page sends it."""
    body = {"choices": [{"file": file, "ticked": on} for file, on in choices]}
    return Call("POST", "/api/phone", json.dumps(body).encode(), JSON_HEADERS)


def _free() -> Call:
    """`POST /api/free`: "Delete from the phone"."""
    return Call("POST", "/api/free", b"{}", JSON_HEADERS)


def test_the_groups_tick_the_pc_s_files_never_a_set_aside(locations: Locations) -> None:
    """Library and import ticked for the user; set aside unticked, its warning shown."""
    state = _session(locations).state()
    assert [group.case for group in state.groups] == [
        PhoneCase.LIBRARY,
        PhoneCase.DESTINATION,
        PhoneCase.SET_ASIDE,
    ]
    assert [(tile.name, tile.ticked) for tile in state.tiles] == [
        ("IMG_1.jpg", True),
        ("IMG_2.jpg", True),
        ("burst.jpg", False),
    ]
    aside = state.tiles[2]
    assert "lost for good" in aside.warning
    assert aside.preview == ""  # a generic tile
    assert state.tiles[0].held == _LIBRARY
    assert state.tiles[0].preview.startswith("/preview/")
    saved, _stamp = read_phone_decisions(locations.reports_dir / PHONE_DECISIONS)
    assert [(c.path, c.ticked) for c in saved.files] == [
        ("Camera/IMG_1.jpg", True),
        ("Camera/IMG_2.jpg", True),
        ("Camera/burst.jpg", False),
    ]


def test_each_tick_is_saved_read_back_and_a_forged_one_refused(
    locations: Locations,
) -> None:
    """The answer is the file read back; a file the page does not show: 422."""
    session = _session(locations)
    page, state, ticked, held, forged, empty, other = serve_app_and_call(
        lambda pool: PhoneApp(session, PAGE, pool),
        [
            Call("GET", "/"),
            Call("GET", "/api/state"),
            _tick((0, False), (2, True)),
            Call("GET", "/api/file"),
            _tick((7, True)),
            Call("POST", "/api/phone", b'{"choices": []}', JSON_HEADERS),
            Call("POST", "/api/phone", b"{}", ("Host: example.com", *JSON_HEADERS[1:])),
        ],
    )
    assert (page.status, len(json.loads(state.body)["tiles"])) == (200, 3)
    reply = json.loads(ticked.body)
    assert (reply["ticked"], reply["bytes"], reply["total"]) == (2, 200, 3)
    assert reply["file"]["ticked"] == [1, 2]
    assert json.loads(held.body)["ticked"] == [1, 2]
    assert (forged.status, empty.status, other.status) == (422, 400, 403)
    assert session.ticked_lines() == (_PLAN[2], _PLAN[3])


def test_the_preview_shows_the_library_s_file(locations: Locations) -> None:
    """The tile of a file the library holds: a JPEG of the PC's file."""
    session = _session(locations)
    path = session.state().tiles[0].preview
    (shown,) = serve_app_and_call(
        lambda pool: PhoneApp(session, PAGE, pool), [Call("GET", path)]
    )
    assert shown.status == 200
    assert shown.body.startswith(b"\xff\xd8")


def test_delete_needs_a_tick_and_the_file_read_back(locations: Locations) -> None:
    """Nothing ticked: "Delete" refused, every time; the page goes on."""
    session = _session(locations)
    none, refused, freed = serve_app_and_call(
        lambda pool: PhoneApp(session, PAGE, pool),
        [_tick((0, False), (1, False)), _free(), _free()],
    )
    assert json.loads(none.body)["ticked"] == 0
    assert refused.status == 422
    assert "Nothing is ticked" in json.loads(refused.body)["error"]
    assert freed.status == 422
    assert not session.freeing
    assert not session.ticked_lines()


def _serve(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> tuple[threading.Thread, int, list[tuple[str, ...]]]:
    """Run `serve_phone_review` in a thread; its port, and where its result lands."""
    write_shot(locations.data_dir / "c/Photos/2025/IMG_1.jpg", Shot(7))
    runtime = make_runtime(locations)
    ports: queue.Queue[int] = queue.Queue()

    def told(port: int) -> str:
        ports.put(port)
        return f"http://127.0.0.1:{port}/"

    monkeypatch.setattr(phone_review, "page_url", told)
    files, _skipped = read_ticked(_PLAN)
    results: list[tuple[str, ...]] = []
    thread = threading.Thread(
        target=lambda: results.append(
            serve_phone_review(runtime, PhoneReview(_PHONE, files, None, 0))
        )
    )
    thread.start()
    return thread, ports.get(timeout=10), results


def test_delete_from_the_phone_ends_the_page_with_the_files_ticked(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """On Delete the page ends, `mh` gets the lines the file on the disk holds."""
    thread, port, results = _serve(locations, monkeypatch)
    page = asyncio.run(send_call(port, Call("GET", "/")))
    assert b"/api/free" in page.body
    freed = asyncio.run(send_call(port, _free()))
    thread.join(timeout=10)
    assert freed.status == 200
    assert results == [(_PLAN[0], _PLAN[2])]


def test_leaving_the_page_deletes_nothing(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """On Leave everything the page ends, no line for `mh`."""
    thread, port, results = _serve(locations, monkeypatch)
    asyncio.run(send_call(port, Call("POST", "/api/stop", b"{}", JSON_HEADERS)))
    thread.join(timeout=10)
    assert results == [()]


def test_phone_review_without_a_file_the_pc_holds_serves_nothing(
    locations: Locations, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Only new files: no page, nothing printed."""
    point_mounts(locations, monkeypatch)
    result = CliRunner().invoke(
        build_app(),
        [PHONE_REVIEW, "--phone", _PHONE],
        input=_line(PhoneCase.NEW, "a.jpg") + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert result.stdout == ""
    assert "nothing to free" in result.stderr
    assert not (tmp_path / "reports" / PHONE_DECISIONS).exists()
