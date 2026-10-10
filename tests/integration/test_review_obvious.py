"""`review`: obvious series and their reasons, validated in one write, undone whole."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.report.decisions import BurstStatus, read_decisions
from tests.support.review import (
    BURST,
    JSON_HEADERS,
    Call,
    review_session,
    serve_and_call,
    write_burst,
)
from tests.support.scenes import Shot, write_shot

if TYPE_CHECKING:
    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations

OTHER: Final = "c/Photos/Autre"
# Blurriness only, eagerly: the blurred shot is proposed, the others kept.
EAGER: Final[Layer] = {"review": {"propose_aside_below": 0.99, "identical_below": 0}}
# Every shot of a series is a repeat of its sharpest: the series is obvious.
REPEATS: Final[Layer] = {"review": {"identical_below": 64}}


def batch(choices: dict[int, list[int] | None]) -> Call:
    """`POST /api/decide` with every choice in one body, as the page sends a batch."""
    body = [{"series": series, "discarded": aside} for series, aside in choices.items()]
    return Call(
        "POST", "/api/decide", json.dumps({"choices": body}).encode(), JSON_HEADERS
    )


def write_second_burst(locations: Locations) -> None:
    """Two shots of another scene, in another folder, a second apart."""
    for rank in range(2):
        write_shot(
            locations.data_dir / f"{OTHER}/IMG_{rank}.jpg",
            Shot(300, shift=3 * rank, taken_at=f"2022:01:02 09:00:0{rank}"),
        )


def test_obvious_series_are_validated_in_one_write_then_undone(
    locations: Locations,
) -> None:
    """Two obvious series: one write holds both, read back; one undo, both todo."""
    write_burst(locations.data_dir)
    write_second_burst(locations)
    session = review_session(locations, REPEATS)
    series = session.state().series
    assert [item.obvious for item in series] == [True, True]
    proposals = {
        number: [rank for rank, shot in enumerate(item.shots) if shot.proposed]
        for number, item in enumerate(series)
    }
    target = locations.reports_dir / "decisions.json"
    done, undone = serve_and_call(
        session, [batch(dict(proposals)), batch(dict.fromkeys(proposals))]
    )
    assert (done.status, undone.status) == (200, 200)
    body = done.json()
    assert isinstance(body, dict)
    assert [entry["status"] for entry in body["file"]["entries"]] == ["done", "done"]
    after = undone.json()
    assert isinstance(after, dict)
    assert [entry["status"] for entry in after["file"]["entries"]] == ["todo", "todo"]
    assert all(
        burst.status is BurstStatus.TODO for burst in read_decisions(target).bursts
    )
    assert session.seen == (0, 2)


def test_a_shot_that_differs_leaves_the_series_to_look_at(
    locations: Locations,
) -> None:
    """Nothing proposed beside the sharpest: to look at, nothing written as a reason."""
    write_burst(locations.data_dir)
    zero: dict[str, object] = dict.fromkeys(
        ("propose_aside_below", "identical_below"), 0
    )
    session = review_session(locations, {"review": zero})
    [item] = session.state().series
    assert not item.obvious
    assert all(shot.reason == "" for shot in item.shots)


def test_reasons_stay_in_the_page_never_in_the_file(locations: Locations) -> None:
    """A proposed shot carries its reason; decisions.json lists names only."""
    write_burst(locations.data_dir)
    session = review_session(locations, EAGER)
    [item] = session.state().series
    reasons = {shot.reason for shot in item.shots if shot.proposed}
    assert reasons == {"blurrier"}
    session.decide(
        {0: frozenset(rank for rank, shot in enumerate(item.shots) if shot.proposed)}
    )
    text = (locations.reports_dir / "decisions.json").read_text()
    assert "blurrier" not in text
    assert BURST.rsplit("/", 1)[-1] in text
