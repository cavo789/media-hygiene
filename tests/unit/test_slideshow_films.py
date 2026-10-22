"""The videos of the slideshow (0292): played as they are, never transcoded.

A phone's `.mov` is served as `video/mp4` (a Chromecast's browser downloads a
`video/quicktime` one); a video the TV cannot play (HEVC) is passed over and labelled
on the phone; the timer waits for the TV to say the video ended; a TV whose browser
plays no video (a 2012 TV's own) makes the show pass over its videos.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import pytest
from PIL import Image

from media_hygiene.index.schema import prepare
from media_hygiene.review.ending import Ending, EndingDoor
from media_hygiene.review.http import ContentType, Request, Response
from media_hygiene.review.lan import COOKIE_NAME, LanAccess
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.pictures import Pictures
from media_hygiene.slideshow.app import ShowPages, SlideshowApp
from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.door import Door
from media_hygiene.slideshow.films import film_ended
from media_hygiene.slideshow.pictures import ShowPictures
from media_hygiene.slideshow.screen_jpeg import ScreenJob
from media_hygiene.slideshow.screens import SCREEN_COOKIE, Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import (
    UNKNOWN_LENGTH_SECONDS,
    Film,
    Slide,
    Timing,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_INTERVAL: Final = 8.0
_PORT: Final = 8090
_ACCESS: Final = LanAccess("10.0.0.5", _PORT, b"ef" * 32)
_PC: Final = f"127.0.0.1:{_PORT}"
_FILM_BYTES: Final = bytes(range(256)) * 4
# Their row is their key: a photo, a phone's H.264 `.mov`, an HEVC `.mp4`, a photo.
_FILES: Final = ("a.jpg", "phone.MOV", "hevc.mp4", "b.jpg")
_H264: Final = Film(".mov", "h264", 20.0)
_HEVC: Final = Film(".mp4", "hevc", 9.0)


class _Clock:
    """A clock the test moves by hand."""

    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


def _slides() -> tuple[Slide, ...]:
    return (Slide(1), Slide(2, film=_H264), Slide(3, film=_HEVC), Slide(4))


def _show(clock: _Clock) -> Show:
    return Show(_slides(), Timing(_INTERVAL, clock))


def _key(show: Show) -> int | None:
    return None if show.current is None else show.current.key


def test_a_film_plays_when_its_container_and_codec_play_on_the_tv() -> None:
    """H.264 in MP4/MOV/WebM: played; HEVC, an AVI: not; an unknown codec: tried."""
    assert _H264.playable
    assert Film(".webm", "vp9").playable
    assert Film(".mp4").playable
    assert not _HEVC.playable
    assert not Film(".avi", "h264").playable
    assert _HEVC.label == "hevc"
    assert Film(".avi", "h264").label == "avi"


def test_an_hevc_video_is_passed_over_and_cannot_be_chosen() -> None:
    """Next goes from the H.264 video to the last photo; a jump to it is refused."""
    show = _show(_Clock())
    show.move(1)
    assert _key(show) == 2
    assert show.upcoming == Slide(4)
    show.move(1)
    assert _key(show) == 4
    assert not show.jump(3)
    assert _key(show) == 4
    assert Show((Slide(3, film=_HEVC), Slide(1)), Timing(_INTERVAL)).current == Slide(1)


def test_the_timer_waits_for_the_end_of_the_video() -> None:
    """Playing: a photo stays the interval, a video until the TV says it ended."""
    clock = _Clock()
    show = _show(clock)
    show.play(playing=True)
    clock.now += _INTERVAL
    assert show.tick()
    assert _key(show) == 2
    clock.now += _INTERVAL * 2  # past a photo's interval, within the video's length
    assert not show.tick()
    assert not film_ended(show, 1)  # another key: nothing
    assert film_ended(show, 2)
    assert _key(show) == 4


def test_a_video_ended_while_paused_stays_and_a_silent_tv_is_not_waited_forever() -> (
    None
):
    """Paused: the TV's end does not move the show; playing, the length and a margin."""
    clock = _Clock()
    show = _show(clock)
    assert show.jump(2)
    assert not film_ended(show, 2)
    assert _key(show) == 2
    show.play(playing=True)
    clock.now += 20.0 + 14.0
    assert not show.tick()
    clock.now += 1.0  # its 20 s and 15 s more: the TV is gone
    assert show.tick()
    assert _key(show) == 4
    timing = Timing(_INTERVAL)
    assert timing.stay(Slide(9, film=Film(".mp4"))) == UNKNOWN_LENGTH_SECONDS
    assert timing.stay(Slide(9, film=Film(".mp4", "h264", 100.0))) == 150.0
    assert timing.stay(None) == _INTERVAL


def _films(screens: Screens) -> bool:
    """Read the property afresh: mypy would keep its last asserted value."""
    return screens.films


def test_every_tv_showing_photos_only_passes_over_the_videos() -> None:
    """One photos-only TV: the video on it moves on; a TV that plays them: back."""
    screens = Screens()
    assert screens.films  # no TV yet
    token = screens.arrive("")
    assert token is not None
    code = screens.code_of(token)
    assert code is not None
    screens.tell(token, films=False)  # not paired yet: not recorded
    assert screens.confirm(code)
    screens.tell(token, films=False)
    assert not _films(screens)
    screens.tell(token, films=True)
    assert _films(screens)


@pytest.fixture
def app(tmp_path: Path) -> Iterator[SlideshowApp]:
    """A show of two photos and two videos, the PC on the home network."""
    index = tmp_path / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        prepare(connection)
        for name in _FILES:
            path = tmp_path / name
            if name.endswith(".jpg"):
                Image.new("RGB", (64, 48), (120, 0, 0)).save(path)
            else:
                path.write_bytes(_FILM_BYTES)
            connection.execute(
                "INSERT INTO files (path, size, mtime_ns) VALUES (?, ?, 1)",
                (str(path), path.stat().st_size),
            )
        connection.commit()
    show = Show(_slides(), Timing(_INTERVAL))
    screens = Screens()
    keys = frozenset(slide.key for slide in show.slides)
    with SearchIndex.open(index) as search, ThreadPoolExecutor(1) as executor:
        pictures = ShowPictures(
            keys, Pictures(search, None, executor), ScreenJob(640, None), executor
        )
        yield SlideshowApp(
            Desk(show, screens, Changes()),
            Door(_ACCESS, screens),
            ShowPages(b"remote", b"screen"),
            pictures,
        )


def _get(
    app: SlideshowApp, path: str, headers: dict[str, str] | None = None
) -> Response:
    request = Request("GET", path, {"host": _PC, **(headers or {})})
    return asyncio.run(EndingDoor(app, Ending()).handle(request))


def test_a_mov_is_served_as_mp4_piece_by_piece(app: SlideshowApp) -> None:
    """`video/mp4`, 206 for a range; a photo's key, another suffix: 404."""
    whole = _get(app, "/film/2.mov")
    assert whole.status is HTTPStatus.OK
    assert whole.content_type is ContentType.MP4
    assert "media-src 'self'" in whole.policy
    part = _get(app, "/film/2.mov", {"range": "bytes=0-9"})
    assert part.status is HTTPStatus.PARTIAL_CONTENT
    assert part.part is not None
    assert part.part.length == 10
    for path in ("/film/1.jpg", "/film/2.mp4", "/film/9.mov", "/film/x.mov"):
        assert _get(app, path).status is HTTPStatus.NOT_FOUND, path
    assert "media-src 'self'" in _get(app, "/screen").policy
    assert "media-src 'self'" in _get(app, "/").policy


def test_the_phone_sees_the_videos_marked_and_the_hevc_one_labelled(
    app: SlideshowApp,
) -> None:
    """The H.264 video: its address; the HEVC one: none, its format to say why."""
    slides = json.loads(_get(app, "/api/slides").body)["slides"]
    assert [(slide["thumb"], slide["film"], slide["format"]) for slide in slides] == [
        ("/thumb/1.jpg", "", ""),
        ("", "/film/2.mov", "h264"),
        ("", "", "hevc"),
        ("/thumb/4.jpg", "", ""),
    ]


def test_the_tv_plays_the_video_and_says_when_it_ended(app: SlideshowApp) -> None:
    """The view names the video and the next photo to load; its end moves the show."""
    app.desk.show.play(playing=True)
    assert app.desk.show.jump(2)
    view = json.loads(_get(app, "/api/wait/0").body)
    assert (view["key"], view["photo"], view["film"], view["next"]) == (
        2,
        "",
        "/film/2.mov",
        "/tv/4.jpg",
    )
    assert view["playing"]
    moved = json.loads(_get(app, "/api/ended/2").body)
    assert moved["photo"] == "/tv/4.jpg"
    assert json.loads(_get(app, "/api/ended/2").body)["key"] == 4  # said twice: once


def test_a_photos_only_tv_makes_the_show_pass_over_the_videos(
    app: SlideshowApp,
) -> None:
    """Paired, it asks `/photos`: the video shown moves on, the remote says why."""
    lan = _ACCESS.host
    tv_page = _get(app, "/screen", {"host": lan})
    line = next(line for line in tv_page.headers if line.startswith("Set-Cookie:"))
    token = line.split(f"{SCREEN_COOKIE}=", 1)[1].split(";", 1)[0]
    code = app.desk.screens.code_of(token)
    assert code is not None
    assert app.desk.screens.confirm(code)
    assert app.desk.show.jump(2)
    tv = {"host": lan, "cookie": f"{SCREEN_COOKIE}={token}"}
    view = json.loads(_get(app, "/api/wait/0/photos", tv).body)
    assert view["photo"] == "/tv/4.jpg"
    assert not app.desk.show.films
    assert not json.loads(_get(app, "/api/show/0").body)["films"]
    assert not app.desk.show.jump(2)
    phone = {"host": lan, "cookie": f"{COOKIE_NAME}={_ACCESS.token}"}
    assert app.desk.show.jump(1)
    assert _get(app, "/api/ended/1", phone).status is HTTPStatus.NOT_FOUND
    assert _get(app, "/api/wait/0", tv).status is HTTPStatus.OK
    assert app.desk.show.films  # the same TV now says it plays them
