"""`review` at speed: originals, shots proposed aside, undo, a folder at once."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.report.burst_decisions import BurstStatus
from media_hygiene.report.decisions import read_decisions
from tests.support.review import (
    JSON_HEADERS,
    Call,
    review_session,
    serve_and_call,
    write_burst,
)

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

BLURRED = 1  # the middle shot of the test burst
NO_PROPOSAL = (
    "propose_aside_below",
    "identical_below",
    "brightness_gap",
    "clipped_gap",
)


def choices(*pairs: tuple[int, list[int] | None]) -> Call:
    """`POST /api/decide` with several choices, as the page sends them."""
    body = [{"series": series, "discarded": aside} for series, aside in pairs]
    return Call(
        "POST", "/api/decide", json.dumps({"choices": body}).encode(), JSON_HEADERS
    )


def test_the_original_is_the_file_itself(locations: Locations) -> None:
    """Bytes untouched, cached; an unknown key or another extension: 404."""
    shots = write_burst(locations.data_dir)
    session = review_session(locations)
    original = session.state().series[0].shots[0].original
    found, unknown, other = serve_and_call(
        session,
        [
            Call("GET", original),
            Call("GET", "/original/0123.jpg"),
            Call("GET", original.removesuffix(".jpg") + ".png"),
        ],
    )
    assert (found.status, found.headers["content-type"]) == (200, "image/jpeg")
    assert found.body == shots[0].read_bytes()
    assert found.headers["cache-control"] == "private, no-cache"
    assert (unknown.status, other.status) == (404, 404)


def test_a_vanished_original_is_not_found(locations: Locations) -> None:
    """Deleted since the audit: 404, never an error page."""
    shots = write_burst(locations.data_dir)
    session = review_session(locations)
    original = session.state().series[0].shots[0].original
    shots[0].unlink()
    [reply] = serve_and_call(session, [Call("GET", original)])
    assert reply.status == 404


def test_a_far_less_sharp_shot_is_proposed_aside(locations: Locations) -> None:
    """Below the share of the sharpest: proposed; all 0: never; protected: never."""
    write_burst(locations.data_dir)
    eager = review_session(locations, {"review": {"propose_aside_below": 0.99}})
    shots = eager.state().series[0].shots
    assert shots[BLURRED].proposed
    assert shots[BLURRED].share < 1
    assert not any(shot.proposed for shot in shots if shot.best)
    never = review_session(locations, {"review": dict.fromkeys(NO_PROPOSAL, 0)})
    assert not any(shot.proposed for shot in never.state().series[0].shots)
    eager_and_protected: dict[str, dict[str, object]] = {
        "folders": {"protected": [shots[0].folder]},
        "review": {"propose_aside_below": 0.99},
    }
    guarded = review_session(locations, eager_and_protected)
    assert not any(shot.proposed for shot in guarded.state().series[0].shots)


def test_undo_brings_a_series_back_to_still_to_see(locations: Locations) -> None:
    """`discarded: null`: the series is listed `todo` again, read back as such."""
    write_burst(locations.data_dir)
    target = locations.reports_dir / "decisions.json"
    session = review_session(locations)
    chosen, undone = serve_and_call(session, [choices((0, [1])), choices((0, None))])
    assert (chosen.status, undone.status) == (200, 200)
    body = undone.json()
    assert isinstance(body, dict)
    assert body["file"]["entries"][0]["status"] == "todo"
    [burst] = read_decisions(target).bursts
    assert (burst.status, burst.discarded) == (BurstStatus.TODO, ())
    assert session.seen == (0, 1)


def test_an_impossible_choice_saves_nothing_of_the_group(
    locations: Locations,
) -> None:
    """One unknown series among the choices: refused whole, the file untouched."""
    write_burst(locations.data_dir)
    session = review_session(locations)
    target = locations.reports_dir / "decisions.json"
    before = target.read_bytes()
    [reply] = serve_and_call(session, [choices((0, [1]), (7, []))])
    assert reply.status == 422
    assert target.read_bytes() == before
