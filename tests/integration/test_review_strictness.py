"""The thresholds of `review` and `review --junk`, tried on the page, then kept."""

from __future__ import annotations

import json
import re
import tomllib
from typing import TYPE_CHECKING, Final, cast

from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.app import ReviewApp
from media_hygiene.review.strictness import STRICTNESS_PATH
from media_hygiene.review.unwanted_app import UnwantedApp
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.review_file import review_page
from media_hygiene.services.reviewing import BURST_KEYS
from media_hygiene.services.unwanted_reviewing import (
    UNWANTED_KEYS,
    open_unwanted_review,
)
from tests.integration.test_unwanted_review import NIGHT, add_unwanted
from tests.support.review import (
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
    from media_hygiene.review.session import ReviewSession
    from media_hygiene.review.unwanted_session import UnwantedSession

EAGER: Final = {"propose_aside_below": 0.99, "identical_below": 0}
COMMENT: Final = "# my own note\n[review]\nport = 8099\n"


def tune(values: dict[str, float | bool], *, save: bool = False) -> Call:
    """`POST /api/strictness`, as the page sends it."""
    body = json.dumps({"values": values, "save": save}).encode()
    return Call("POST", STRICTNESS_PATH, body, JSON_HEADERS)


def serve_bursts(session: ReviewSession, *calls: Call) -> list[dict[str, object]]:
    """The answers of a burst review's server, as JSON."""
    replies = serve_app_and_call(lambda pool: ReviewApp(session, PAGE, pool), calls)
    return [cast("dict[str, object]", reply.json()) for reply in replies]


def proposed(session: ReviewSession) -> list[str]:
    """The shots proposed aside, by name."""
    return [
        shot.name
        for item in session.state().series
        for shot in item.shots
        if shot.proposed
    ]


def test_trying_a_value_moves_the_proposals_and_writes_nothing(
    locations: Locations,
) -> None:
    """Live: the shot enters, is named; nothing on disk."""
    write_burst(locations.data_dir)
    session = review_session(
        locations, {"review": {"propose_aside_below": 0.0, "identical_below": 0}}
    )
    assert proposed(session) == []
    reply = serve_bursts(session, tune(EAGER))[0]
    assert proposed(session)
    assert reply["entered"] == {
        "count": len(proposed(session)),
        "names": proposed(session),
    }
    assert reply["values"] == EAGER
    assert not locations.config_file.exists()


def test_a_choice_made_stays_and_its_series_counts_for_nothing(
    locations: Locations,
) -> None:
    """A series seen keeps its choice in memory and on disk, whatever the thresholds."""
    write_burst(locations.data_dir)
    session = review_session(locations, {"review": {"identical_below": 0}})
    replies = serve_app_and_call(
        lambda pool: ReviewApp(session, PAGE, pool),
        [decide(0, 2), tune(EAGER)],
    )
    assert cast("dict[str, dict[str, int]]", replies[1].json())["entered"]["count"] == 0
    assert session.state().series[0].discarded == (2,)
    target = locations.reports_dir / "decisions.json"
    assert read_decisions(target).bursts[0].discarded


def test_keeping_values_keeps_comments_and_reads_the_file_back(
    locations: Locations,
) -> None:
    """Only what changed is written, in `[review]`; the answer is the disk's."""
    write_burst(locations.data_dir)
    locations.config_file.parent.mkdir(parents=True, exist_ok=True)
    locations.config_file.write_text(COMMENT, encoding="utf-8")
    session = review_session(locations)
    reply = serve_bursts(session, tune({"identical_below": 9}, save=True))[0]
    text = locations.config_file.read_text(encoding="utf-8")
    assert "# my own note" in text
    assert tomllib.loads(text)["review"] == {"port": 8099, "identical_below": 9}
    assert reply["proof"] == {"identical_below": 9}
    assert cast("dict[str, int]", reply["saved"])["identical_below"] == 9


def test_refused_values_and_keys_change_nothing(locations: Locations) -> None:
    """Out of bounds, or a key of another page: 422 with the reason; no file."""
    write_burst(locations.data_dir)
    session = review_session(locations)
    replies = serve_app_and_call(
        lambda pool: ReviewApp(session, PAGE, pool),
        [
            tune({"identical_below": 99}, save=True),
            tune({"port": 1}, save=True),
            Call("POST", STRICTNESS_PATH, b"[]", JSON_HEADERS),
        ],
    )
    assert [reply.status for reply in replies] == [422, 422, 400]
    assert not locations.config_file.exists()


def junk_session(locations: Locations) -> UnwantedSession:
    """`review --junk` on a nearly black photo and a screenshot."""
    add_unwanted(locations.data_dir)
    runtime = make_runtime(locations)
    findings = AuditService(runtime, NullProgress()).run()
    return open_unwanted_review(
        runtime, findings, locations.reports_dir / "decisions.json"
    )


def names(session: UnwantedSession) -> set[str]:
    """The photos of the page."""
    return {photo.name for photo in session.state().photos}


def serve_junk(session: UnwantedSession, *calls: Call) -> list[dict[str, object]]:
    """The answers of an unwanted review's server, as JSON."""
    replies = serve_app_and_call(lambda pool: UnwantedApp(session, PAGE, pool), calls)
    return [cast("dict[str, object]", reply.json()) for reply in replies]


def test_unwanted_group_says_who_leaves_then_saves_under_its_section(
    locations: Locations,
) -> None:
    """Disabling a reason: its photo leaves, is named; saved in `[review.unwanted]`."""
    session = junk_session(locations)
    night = NIGHT.rsplit("/", 1)[1]
    assert night in names(session)
    left, kept = serve_junk(
        session,
        tune({"dark_mean": 0, "blur_percentile": 0}),
        tune({"dark_mean": 0, "blur_percentile": 0}, save=True),
    )
    assert night in cast("dict[str, list[str]]", left["left"])["names"]
    assert night not in names(session)
    assert kept["proof"] == {"dark_mean": 0.0, "blur_percentile": 0.0}
    held = tomllib.loads(locations.config_file.read_text(encoding="utf-8"))
    assert held["review"]["unwanted"]["dark_mean"] == 0


def test_a_photo_decided_stays_listed_when_its_reason_goes(
    locations: Locations,
) -> None:
    """Set aside, then its reason disabled: still shown and in the file."""
    session = junk_session(locations)
    night = NIGHT.rsplit("/", 1)[1]
    rank = next(
        rank for rank, photo in enumerate(session.state().photos) if photo.name == night
    )
    session.decide({rank: True})
    serve_junk(session, tune({"dark_mean": 0, "blur_percentile": 0}))
    photos = session.state().photos
    assert [photo.decision for photo in photos if photo.name == night] == ["aside"]
    target = locations.reports_dir / "decisions.json"
    assert [entry.aside for entry in read_decisions(target).unwanted] == [True]
    assert session.decided[1] == 1


def test_both_pages_offer_the_sliders_on_the_keys_their_server_changes(
    locations: Locations,
) -> None:
    """Each slider of a page names a key its server accepts, on the route."""
    write_burst(locations.data_dir)
    session = review_session(locations)
    bursts = review_page(
        "review.html.j2",
        session.place,
        ("/api/decide", "/api/file"),
    ).decode()
    junk = review_page(
        "unwanted_review.html.j2", session.place, ("/api/junk", "/api/file")
    ).decode()
    for page, keys in ((bursts, BURST_KEYS), (junk, UNWANTED_KEYS)):
        assert set(re.findall(r'data-name="(\w+)"', page)) == set(keys)
        assert f'"{STRICTNESS_PATH}"' in page
