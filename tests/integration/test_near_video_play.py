"""`review --near` plays re-encoded videos: by parts, plan files only, own CSP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.review.near_app import NearApp
from media_hygiene.review.respond import CHUNK
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.near_reviewing import open_near_review
from tests.support.media import FFMPEG
from tests.support.near_videos import ORIGINAL, write_near_videos
from tests.support.review import PAGE, Call, serve_and_call, serve_app_and_call
from tests.support.review import review_session as burst_session
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.near_session import NearSession

pytestmark = [
    pytest.mark.skipif(FFMPEG is None, reason="ffmpeg writes the videos"),
    pytest.mark.usefixtures("cli"),
]
MEDIA: Final = "media-src 'self'"


def ranged(path: str, bytes_range: str) -> Call:
    """`GET` with a `Range` header, as a browser seeking in a video sends it."""
    return Call("GET", path, headers=("Host: 127.0.0.1", f"Range: {bytes_range}"))


def video_session(locations: Locations) -> NearSession:
    """Write the videos, audit them and open `review --near`."""
    write_near_videos(locations.data_dir)
    runtime = make_runtime(locations)
    findings = AuditService(runtime, NullProgress()).run()
    return open_near_review(runtime, findings, locations.reports_dir / "decisions.json")


def test_both_versions_play_and_seek(locations: Locations) -> None:
    """Whole with its media type, a part as 206, the last bytes, beyond the end: 416."""
    session = video_session(locations)
    [group] = [g for g in session.state().groups if g.kept.name == "Plage.mp4"]
    [copy] = group.copies
    data = (locations.data_dir / ORIGINAL).read_bytes()
    size = len(data)
    page, whole, part, tail, beyond, other = serve_app_and_call(
        lambda pool: NearApp(session, PAGE, pool),
        [
            Call("GET", "/"),
            Call("GET", "/" + group.kept.video),
            ranged("/" + group.kept.video, "bytes=100-1099"),
            ranged("/" + group.kept.video, "bytes=-10"),
            ranged("/" + group.kept.video, f"bytes={size}-"),
            ranged("/" + copy.video, "bytes=0-"),
        ],
    )
    assert MEDIA in page.headers["content-security-policy"]
    assert (whole.status, whole.headers["content-type"]) == (200, "video/mp4")
    assert whole.headers["accept-ranges"] == "bytes"
    assert whole.body == data
    assert part.status == 206
    assert part.headers["content-range"] == f"bytes 100-1099/{size}"
    assert part.body == data[100:1100]
    assert (tail.status, tail.body) == (206, data[-10:])
    assert beyond.status == 416
    assert beyond.headers["content-range"] == f"bytes */{size}"
    assert (other.status, other.body[:8]) == (206, copy_bytes(locations)[:8])


def copy_bytes(locations: Locations) -> bytes:
    """The re-encoded copy, as it lies on the disk."""
    return next(locations.data_dir.rglob("VID-*.mp4")).read_bytes()


def test_only_the_videos_of_the_plan_are_served(locations: Locations) -> None:
    """Unknown key, wrong extension, a picture of the plan, a vanished file: 404."""
    session = video_session(locations)
    [group] = [g for g in session.state().groups if g.kept.name == "Plage.mp4"]
    key = group.kept.video.removeprefix("video/").removesuffix(".mp4")
    picture = next(g for g in session.state().groups if g.kept.preview).kept
    picture_key = picture.preview.removeprefix("preview/").removesuffix(".jpg")
    replies = serve_app_and_call(
        lambda pool: NearApp(session, PAGE, pool),
        [
            Call("GET", "/video/0123456789abcdef01234567.mp4"),
            Call("GET", f"/video/{key}.mov"),
            Call("GET", f"/video/{picture_key}.jpg"),
            Call("GET", "/video/../../etc/passwd"),
            Call("GET", group.kept.video, headers=("Host: evil.example",)),
        ],
    )
    assert [reply.status for reply in replies] == [404, 404, 404, 404, 403]
    (locations.data_dir / ORIGINAL).unlink()
    [gone] = serve_app_and_call(
        lambda pool: NearApp(session, PAGE, pool), [Call("GET", group.kept.video)]
    )
    assert gone.status == 404


def test_a_long_video_is_sent_in_chunks(locations: Locations) -> None:
    """A file larger than a chunk arrives whole; a malformed Range is ignored."""
    session = video_session(locations)
    [group] = [g for g in session.state().groups if g.kept.name == "Plage.mp4"]
    source = session.preview_source(
        group.kept.video.removeprefix("video/").removesuffix(".mp4")
    )
    assert source is not None
    padded = source.read_bytes() + bytes(2 * CHUNK)
    source.write_bytes(padded)
    [reply] = serve_app_and_call(
        lambda pool: NearApp(session, PAGE, pool),
        [ranged("/" + group.kept.video, "bytes=0-10,20-30")],
    )
    assert (reply.status, reply.body) == (200, padded)


def test_the_burst_page_keeps_its_stricter_policy(locations: Locations) -> None:
    """The burst review shows photos only: no `media-src`, no video route."""
    [page, video] = serve_and_call(
        burst_session(locations), [Call("GET", "/"), Call("GET", "/video/x.mp4")]
    )
    assert MEDIA not in page.headers["content-security-policy"]
    assert video.status == 404
