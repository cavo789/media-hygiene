"""`review`: the decisions file lists every series; each choice is read back."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.report.burst_decisions import BurstStatus
from media_hygiene.report.decisions import read_decisions
from media_hygiene.review import session as session_module
from tests.support.review import (
    BURST_HOST,
    Call,
    decide,
    review_session,
    serve_and_call,
    write_burst,
)

if TYPE_CHECKING:
    import pytest

    from media_hygiene.paths.locations import Locations

SHOTS = [f"{BURST_HOST}\\IMG_{rank}.jpg" for rank in range(3)]


def test_the_file_lists_every_series_from_the_start(locations: Locations) -> None:
    """Written as the review opens: each series still to see, every shot kept."""
    write_burst(locations.data_dir)
    session = review_session(locations)
    [burst] = read_decisions(locations.reports_dir / "decisions.json").bursts
    assert (burst.status, list(burst.kept), burst.discarded) == (
        BurstStatus.TODO,
        SHOTS,
        (),
    )
    assert session.seen == (0, 1)
    assert not session.state().series[0].reviewed
    resumed = review_session(locations)
    assert (resumed.dropped, resumed.seen) == (0, (0, 1))


def test_each_choice_is_read_back_from_the_disk(locations: Locations) -> None:
    """The answer and `GET /api/file` say what the file on the disk holds."""
    write_burst(locations.data_dir)
    target = locations.reports_dir / "decisions.json"
    chosen, found = serve_and_call(
        review_session(locations), [decide(0, 1), Call("GET", "/api/file")]
    )
    entry = {
        "series": 0,
        "status": "done",
        "kept": [SHOTS[0], SHOTS[2]],
        "discarded": [SHOTS[1]],
    }
    answer, on_disk = chosen.json(), found.json()
    assert isinstance(answer, dict)
    assert isinstance(on_disk, dict)
    assert answer["file"]["entries"] == [entry]
    assert answer["seen"] == answer["total"] == 1
    assert on_disk["entries"] == [entry]
    assert on_disk["size"] == target.stat().st_size


def test_a_choice_missing_from_the_disk_is_an_error(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Saved in memory but not on the disk: the page is told, not reassured."""
    write_burst(locations.data_dir)
    session = review_session(locations)
    monkeypatch.setattr(session_module, "write_decisions", lambda *_args: None)
    [reply] = serve_and_call(session, [decide(0, 1)])
    assert reply.status == 422
    assert b"does not hold your choice" in reply.body


def test_an_unreadable_file_is_reported(locations: Locations) -> None:
    """Spoiled since the review opened: `GET /api/file` explains why."""
    write_burst(locations.data_dir)
    session = review_session(locations)
    target = locations.reports_dir / "decisions.json"
    target.write_text(json.dumps({"version": 1}))
    [reply] = serve_and_call(session, [Call("GET", "/api/file")])
    assert reply.status == 422
    assert b"not a valid decisions file" in reply.body
