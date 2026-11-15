"""The remote's "Avoid some people" (0825): their photos out of the show, and back."""

from __future__ import annotations

import json
from http import HTTPStatus
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.review.http import Request
from media_hygiene.services.slideshow_avoid import named_people
from media_hygiene.slideshow.avoid_desk import (
    AVOID_PATH,
    NO_AVOID,
    PHONE_MARK,
    AvoidDesk,
    Memory,
)
from media_hygiene.slideshow.avoid_memory import remembered
from media_hygiene.slideshow.avoid_seen import Seen
from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.screens import Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Slide, Timing

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_INTERVAL = 8.0
_UNSORTED = ("Fleur", "Émile", "antoine", "Diego", "Fleur")


def _present() -> dict[str, Seen]:
    """Antoine named on photo 2, guessed on 4; Manon only guessed, on 3."""
    return {
        "Antoine": Seen(frozenset({2}), frozenset({4})),
        "Manon": Seen(guessed=frozenset({3})),
    }


def _desk() -> Desk:
    show = Show(tuple(Slide(key) for key in range(1, 6)), Timing(_INTERVAL))
    return Desk(show, Screens(), Changes())


def _post(avoid: AvoidDesk, desk: Desk, names: list[str]) -> dict[str, object]:
    response = avoid.ask(
        desk, Request("POST", AVOID_PATH, {}, json.dumps({"names": names}).encode())
    )
    assert response.status == HTTPStatus.OK
    view: dict[str, object] = json.loads(response.body)
    return view


def test_ticking_sets_their_photos_out_and_unticking_brings_them_back() -> None:
    """Ticking a name greys their photos; unticking it shows them again."""
    desk, avoid = _desk(), AvoidDesk(_present)
    view = _post(avoid, desk, ["Antoine", "Nobody"])
    assert desk.show.skipped == {2, 4}
    people = [
        {"name": "Antoine", "sure": 1, "guessed": 1},
        {"name": "Manon", "sure": 0, "guessed": 1},
    ]
    assert view == {
        "people": people,
        "ticked": ["Antoine"],
        "out": 2,
        "remembered": [],
        "phone": True,  # no config.toml to write: for this show only
    }
    view = _post(avoid, desk, [])
    assert desk.show.skipped == set()
    assert view["out"] == 0


def test_a_photo_set_out_by_hand_stays_out() -> None:
    """Unticking never brings back a photo set out by hand."""
    desk, avoid = _desk(), AvoidDesk(_present)
    desk.show.set_out(4, out=True)
    _post(avoid, desk, ["Antoine"])
    _post(avoid, desk, [])
    assert desk.show.skipped == {4}


def test_a_body_that_is_not_names_is_refused() -> None:
    """A body without names is a 400."""
    desk = _desk()
    assert (
        AvoidDesk(_present).ask(desk, Request("POST", AVOID_PATH, {}, b"[]")).status
        == HTTPStatus.BAD_REQUEST
    )


def test_nobody_named_avoids_nothing() -> None:
    """With nobody named, the block has no name and sets nothing out."""
    desk = _desk()
    view = NO_AVOID.view()
    assert (view["people"], view["ticked"], view["out"]) == ([], [], 0)
    assert desk.show.skipped == set()


def test_the_names_are_alphabetical_case_and_accents_aside() -> None:
    """The names come sorted as a reader expects: Émile between Diego and Fleur."""
    people = SimpleNamespace(person=[SimpleNamespace(name=n) for n in _UNSORTED])
    runtime = cast("Runtime", SimpleNamespace(settings=SimpleNamespace(people=people)))
    assert named_people(runtime) == ["antoine", "Diego", "Émile", "Fleur"]


def test_the_people_are_found_once() -> None:
    """The match runs at the first ask only, not at each tick."""
    calls: list[int] = []

    def counted() -> dict[str, Seen]:
        calls.append(1)
        return _present()

    desk, avoid = _desk(), AvoidDesk(counted)
    avoid.view()
    _post(avoid, desk, ["Manon"])
    assert len(calls) == 1
    assert desk.show.skipped == {3}


def test_the_phone_ticks_for_this_show_only(tmp_path: Path) -> None:
    """0834: a phone's tick sets the photos out, `config.toml` unchanged."""
    config = tmp_path / "config.toml"
    config.write_text("[slideshow]\navoid = ['Manon']\n", "utf-8")
    before = config.read_bytes()
    desk = _desk()
    avoid = AvoidDesk(_present, memory=Memory(config, ["Manon"]))
    avoid.start(desk)
    assert desk.show.skipped == {3}  # remembered: out from the start
    body = json.dumps({"names": ["Antoine"]}).encode()
    phone = Request("POST", AVOID_PATH, {PHONE_MARK: "1"}, body)
    view = json.loads(avoid.ask(desk, phone).body)
    assert desk.show.skipped == {2, 4}
    assert view["phone"] is True
    assert config.read_bytes() == before


def test_the_pc_tick_is_read_back_from_the_disk(tmp_path: Path) -> None:
    """0834: what the remote says remembered is what the file holds."""
    config = tmp_path / "config.toml"
    desk, avoid = _desk(), AvoidDesk(_present, memory=Memory(config))
    view = _post(avoid, desk, ["Manon"])
    assert view["remembered"] == ["Manon"]
    assert remembered(config) == ("Manon",)
    assert not remembered(None)


def test_a_name_removed_refreshes_the_counts_and_brings_the_photo_back() -> None:
    """0830: `fresh` finds the people again: a guess taken off no longer sets it out."""
    found = [_present()]
    desk = _desk()
    avoid = AvoidDesk(lambda: found[-1])
    _post(avoid, desk, ["Antoine"])
    assert desk.show.skipped == {2, 4}
    found.append({"Antoine": Seen(frozenset({2})), "Manon": found[0]["Manon"]})
    body = json.dumps({"names": ["Antoine"], "fresh": True}).encode()
    response = avoid.ask(desk, Request("POST", AVOID_PATH, {}, body))
    view = json.loads(response.body)
    assert view["people"][0] == {"name": "Antoine", "sure": 1, "guessed": 0}
    assert desk.show.skipped == {2}
    assert view["ticked"] == ["Antoine"]
