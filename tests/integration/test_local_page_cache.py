"""Local pages: a picture kept by the browser is reused in its run, never after."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.review.respond import RUN_TAG
from tests.support.review import Call, review_session, serve_and_call, write_burst

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

HOST = "Host: 127.0.0.1"


def asked(tag: str) -> tuple[str, ...]:
    """The headers of a browser holding a copy tagged `tag`."""
    return HOST, f"If-None-Match: {tag}"


def test_a_copy_of_this_run_is_kept_one_of_an_older_run_is_not(
    locations: Locations,
) -> None:
    """Same number, another run (`people` again on the same port): rendered again."""
    write_burst(locations.data_dir)
    session = review_session(locations)
    preview = session.state().series[0].shots[0].preview
    kept, older, video_part = serve_and_call(
        session,
        [
            Call("GET", preview, headers=asked(RUN_TAG)),
            Call("GET", preview, headers=asked('"older"')),
            Call("GET", preview, headers=(*asked(RUN_TAG), "Range: bytes=0-")),
        ],
    )
    assert (kept.status, kept.body, kept.headers["etag"]) == (304, b"", RUN_TAG)
    assert (older.status, older.headers["etag"]) == (200, RUN_TAG)
    assert older.body.startswith(b"\xff\xd8")
    assert video_part.status == 200  # a part asked for is always sent
