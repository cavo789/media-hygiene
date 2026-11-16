"""The remote grouped by event (0832), its photos out last with why (0831)."""

from __future__ import annotations

import json
from http import HTTPStatus

from media_hygiene.review.http import Request
from media_hygiene.slideshow.avoid_desk import AVOID_PATH, AvoidDesk
from media_hygiene.slideshow.avoid_seen import Seen
from media_hygiene.slideshow.chapters import Chapter
from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.pictures import slides_view
from media_hygiene.slideshow.screens import Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Slide, Timing
from tests.support.page_render import render_page

_EASTER = Chapter(1, "Pâques", "avril 2026", folder="2026/2026-04/Pâques")
_SUMMER = Chapter(2, "Vacances", "juillet 2026", folder="2026/2026-07/Vacances")
_AGAIN = Chapter(3, "Pâques", "avril 2026", folder="2026/2026-04/Pâques")


def _desk() -> Desk:
    """Photos 1-2 at Easter, 3-4 in summer, 5 at Easter again, 6 of no event."""
    chapters = (_EASTER, _EASTER, _SUMMER, _SUMMER, _AGAIN, None)
    slides = tuple(Slide(key, chapter=c) for key, c in enumerate(chapters, start=1))
    return Desk(Show(slides, Timing(8.0)), Screens(), Changes())


def _ask(desk: Desk, value: dict[str, object]) -> dict[str, object]:
    response = desk.ask(json.dumps(value).encode())
    assert response.status == HTTPStatus.OK
    state: dict[str, object] = json.loads(response.body)
    return state


def _untick(desk: Desk, folder: str, *, ticked: bool = False) -> dict[str, object]:
    return _ask(desk, {"action": "tick" if ticked else "untick", "folder": folder})


def test_two_events_are_two_groups_in_order_one_per_folder() -> None:
    """Two runs of one folder are one group; a slide of no event has its own."""
    view = slides_view(_desk())
    assert view["events"] == [
        {"folder": "2026/2026-04/Pâques", "name": "Pâques", "period": "avril 2026"},
        {
            "folder": "2026/2026-07/Vacances",
            "name": "Vacances",
            "period": "juillet 2026",
        },
        {"folder": "", "name": "", "period": ""},
    ]
    slides = view["slides"]
    assert isinstance(slides, list)
    assert [slide["folder"] for slide in slides][4:] == ["2026/2026-04/Pâques", ""]


def test_unticking_an_event_sets_out_its_photos_only_and_ticking_back() -> None:
    """Untick: every photo of the folder out, why named; tick: back, but by hand."""
    desk = _desk()
    _ask(desk, {"action": "out", "key": 5})  # by hand
    state = _untick(desk, "2026/2026-04/Pâques")
    assert desk.show.skipped == {1, 2, 5}
    assert state["unticked"] == ["2026/2026-04/Pâques"]
    assert state["why"] == {
        "1": ["event:2026/2026-04/Pâques"],
        "2": ["event:2026/2026-04/Pâques"],
        "5": ["hand"],
    }
    state = _untick(desk, "2026/2026-04/Pâques", ticked=True)
    assert desk.show.skipped == {5}
    assert state["unticked"] == []
    assert state["why"] == {"5": ["hand"]}


def test_an_event_no_photo_is_in_is_not_found() -> None:
    """A folder of no slide: 404, nothing changed."""
    desk = _desk()
    response = desk.ask(b'{"action": "untick", "folder": "nowhere"}')
    assert response.status == HTTPStatus.NOT_FOUND
    assert desk.show.skipped == set()


def _present() -> dict[str, Seen]:
    return {"André": Seen(frozenset({3}), frozenset({4}))}


def test_a_person_ticked_moves_their_photos_out_with_the_reason() -> None:
    """✓ and ≈ name the person; unticking brings them back."""
    desk, avoid = _desk(), AvoidDesk(_present)
    avoid.ask(desk, Request("POST", AVOID_PATH, {}, b'{"names": ["Andr\\u00e9"]}'))
    state = desk.state()
    assert state["why"] == {"3": ["person:✓ André"], "4": ["person:≈ André"]}
    assert avoid.view()["out"] == 2
    avoid.ask(desk, Request("POST", AVOID_PATH, {}, b'{"names": []}'))
    assert desk.show.skipped == set()


def test_show_it_again_wins_while_the_person_stays_ticked() -> None:
    """Shown again by hand: in, even when the names are sent again."""
    desk, avoid = _desk(), AvoidDesk(_present)
    avoid.ask(desk, Request("POST", AVOID_PATH, {}, b'{"names": ["Andr\\u00e9"]}'))
    _ask(desk, {"action": "in", "key": 3})
    avoid.ask(desk, Request("POST", AVOID_PATH, {}, b'{"names": ["Andr\\u00e9"]}'))
    assert desk.show.skipped == {4}


def test_a_photo_of_a_person_and_an_event_stays_out_until_both_are_back() -> None:
    """Out for two groups: ticking one back leaves it out for the other."""
    desk, avoid = _desk(), AvoidDesk(_present)
    avoid.ask(desk, Request("POST", AVOID_PATH, {}, b'{"names": ["Andr\\u00e9"]}'))
    _untick(desk, "2026/2026-07/Vacances")
    avoid.ask(desk, Request("POST", AVOID_PATH, {}, b'{"names": []}'))
    assert desk.show.skipped == {3, 4}
    assert desk.state()["why"] == {
        "3": ["event:2026/2026-07/Vacances"],
        "4": ["event:2026/2026-07/Vacances"],
    }


def test_a_photo_set_out_by_hand_says_by_hand() -> None:
    """*Do not show* on a tile: its reason is `hand`."""
    desk = _desk()
    assert _ask(desk, {"action": "out", "key": 2})["why"] == {"2": ["hand"]}


def test_the_remote_has_no_lone_event_line_and_groups_its_grid() -> None:
    """The lone line is gone; the groups script and the shared look are in."""
    page = render_page("slideshow.html.j2")
    assert 'id="event"' not in page
    assert "function regroup(show)" in page
    assert ".folderBar" in page
    assert "chapter.name, chapter.period" in page  # the status line names it
    assert "Will not be shown" in page


def test_the_phone_page_shares_the_groups_look() -> None:
    """One look of groups of tiles: the phone page includes the same part."""
    assert ".folderBar h2 { margin: 0;" in render_page("phone_review.html.j2")
