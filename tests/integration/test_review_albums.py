"""The burst review adds the shots kept to an album (0295), not those set aside."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.app import ReviewApp
from media_hygiene.services.albums import album_desk
from media_hygiene.share.album_pickers import KeyPicker
from media_hygiene.share.albums import ALBUMS_FILE, read_albums
from tests.support.review import (
    BURST_HOST,
    JSON_HEADERS,
    PAGE,
    Call,
    decide,
    review_session,
    serve_app_and_call,
    write_burst,
)
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_the_shots_kept_go_to_the_album_the_decisions_stay(
    locations: Locations,
) -> None:
    """Keys of the review's previews; the decisions file is not touched by it."""
    write_burst(locations.data_dir)
    session = review_session(locations)
    keys = [
        shot.preview.split("/")[-1].removesuffix(".jpg")
        for shot in session.state().series[0].shots
    ]
    desk = album_desk(make_runtime(locations), KeyPicker(session.preview_source).files)
    body = json.dumps(
        {"action": "add", "album": "Rafale", "keys": [keys[0], keys[2], "nope"]}
    )
    replies = serve_app_and_call(
        lambda pool: ReviewApp(session, PAGE, pool, albums=desk),
        [
            decide(0, 1),
            Call("POST", "/api/albums", body.encode(), JSON_HEADERS),
            Call("GET", "/api/albums"),
            Call("POST", "/api/albums", body.encode(), ("Host: evil.example",)),
        ],
    )
    assert [reply.status for reply in replies] == [200, 200, 200, 403]
    (album,) = read_albums(locations.reports_dir / ALBUMS_FILE).albums
    assert [entry.path for entry in album.entries] == [
        f"{BURST_HOST}\\IMG_0.jpg",
        f"{BURST_HOST}\\IMG_2.jpg",
    ]
    [burst] = read_decisions(locations.reports_dir / "decisions.json").bursts
    assert burst.discarded == (f"{BURST_HOST}\\IMG_1.jpg",)
