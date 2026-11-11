"""A running step shown on every page of the home server (0661).

`review/templates/step_chip.html.j2`: the chip in the header, the tab's title, the end
said, one poll of `GET /api/step` per page (the home page's dialog and *Apply now*
follow it). Included once by the frame, the home page and the album page; a phone
reads it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

from media_hygiene.review.doors import Door
from media_hygiene.review.http import Request
from media_hygiene.review.lan_paths import phone_may
from media_hygiene.review.step_watch import STEP_PATH
from media_hygiene.services import home
from tests.support.page_render import render_page

_TEMPLATES: Final = (
    Path(__file__).parents[2] / "src" / "media_hygiene" / "review" / "templates"
)
_SHARED: Final = (
    '<button type="button" id="mhStepChip"',
    '<dialog id="mhStepDlg"',
    "window.mhStep = Object.freeze(",
    "window.mhNotify = Object.freeze(",
)


@pytest.mark.parametrize(
    "page", ["album.html.j2", "quarantine.html.j2", "search.html.j2"]
)
def test_every_page_holds_the_chip_once_and_a_slot_for_it(page: str) -> None:
    """The frame and the album page: the piece once, the header's slot once."""
    html = render_page(page)
    for part in _SHARED:
        assert html.count(part) == 1, (page, part)
    assert html.count("data-step-slot") == 1 + html.count('"[data-step-slot]"')


def test_the_home_page_holds_it_before_its_script() -> None:
    """The home page's dialog follows the shared poll, so the piece comes first."""
    page = home.home_page().decode()
    for part in _SHARED:
        assert page.count(part) == 1, part
    assert page.index("window.mhStep = ") < page.index("function followStep(")
    assert "window.mhStepOpen = resumeStep;" in page


def test_one_poll_per_page() -> None:
    """The home page's dialog and *Apply now* watch the chip's poll, not their own."""
    chip = (_TEMPLATES / "step_chip.html.j2").read_text("utf-8")
    assert f'const STEP_PATH = "{STEP_PATH}";' in chip
    assert chip.count("fetch(") == 1
    run = (_TEMPLATES / "home_run.js.j2").read_text("utf-8")
    apply = (_TEMPLATES / "apply_now.html.j2").read_text("utf-8")
    for script in (run, apply):
        assert "window.mhStep.watch(" in script
        assert "window.mhStep.claim(" in script
    assert "fetch(P.step" not in run
    assert "fetch(state.follow" not in apply
    notify = (_TEMPLATES / "home_notify.js.j2").read_text("utf-8")
    assert "Notification" not in notify  # the one code is the chip's


def test_a_step_is_shown_as_text_never_html() -> None:
    """A stage or a file name with markup shows as text (0671)."""
    chip = (_TEMPLATES / "step_chip.html.j2").read_text("utf-8")
    assert "innerHTML" not in chip
    assert "insertAdjacentHTML" not in chip


def test_the_hidden_tab_polls_slower_and_a_server_without_steps_not_at_all() -> None:
    """Hidden: a slower poll; 404: none; the poll comes back with the tab."""
    chip = (_TEMPLATES / "step_chip.html.j2").read_text("utf-8")
    assert "if (document.hidden) return HIDDEN_MS;" in chip
    assert "response.status === 404" in chip
    assert 'document.addEventListener("visibilitychange"' in chip


def test_a_phone_reads_the_step_but_never_starts_or_stops_one() -> None:
    """`GET /api/step` is a read; its `POST` and Stop stay the PC's."""
    assert phone_may(Request("GET", STEP_PATH, {}, b"", Door.LAN))
    assert not phone_may(Request("POST", STEP_PATH, {}, b"", Door.LAN))
    chip = (_TEMPLATES / "step_chip.html.j2").read_text("utf-8")
    assert "method:" not in chip  # no POST from the chip: nothing to stop
