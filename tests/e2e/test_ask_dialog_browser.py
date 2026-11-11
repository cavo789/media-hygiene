"""The shared page pieces in Chromium: ask, busy, view in the URL, a step running.

Ask (0663), busy (0664), the view in the URL (0666), a step on every page (0661),
the controls visible at load and the bar menus (0665).

Heavy (the Playwright image): CI only, where `MEDIA_HYGIENE_E2E_BROWSER` is set.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import pytest

from tests.support.page_render import render_page
from tests.support.pages_browser import BrowserRun, build_browser, run_browser

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("MEDIA_HYGIENE_E2E_BROWSER", "") != "1",
        reason="browser tests run in CI only (MEDIA_HYGIENE_E2E_BROWSER=1)",
    ),
]
_SUPPORT: Final = Path(__file__).parents[1] / "support"


def _walk(tmp_path: Path, walk: str, template: str = "quarantine.html.j2") -> str:
    """Run `tests/support/<walk>` on a page (purge by default) in Chromium."""
    page = tmp_path / "quarantine.html"  # the name the browser's container reads
    page.write_text(render_page(template), "utf-8")
    shots = tmp_path / "shots"
    shots.mkdir()
    build_browser()
    run = BrowserRun(
        name="media-hygiene-" + walk.removesuffix(".py").replace("_", "-"),
        scripts=(_SUPPORT / walk, page),
        args=("/tmp/quarantine.html",),  # noqa: S108  # inside the browser's container
        network="bridge",  # the script installs playwright first,
    )
    return run_browser(run, shots)


def test_esc_and_the_safe_button_answer_no(tmp_path: Path) -> None:
    """The purge page's question: Esc, Cancel → no; only the verb button → yes."""
    assert _walk(tmp_path, "ask_walk.py") == ""


def test_a_slow_answer_keeps_the_button_busy(tmp_path: Path) -> None:
    """An answer after 2 s: button disabled, placeholders shown, the grid stays."""
    assert _walk(tmp_path, "busy_walk.py") == ""


def test_the_view_survives_a_reload_and_back_closes_the_large_view(
    tmp_path: Path,
) -> None:
    """A group kept by the URL; Back closes the large view, the grid stays (0666)."""
    assert _walk(tmp_path, "view_walk.py") == ""


def test_the_people_page_keeps_the_view_like_the_other_frame_pages(
    tmp_path: Path,
) -> None:
    """People on the frame (0667): the URL kept, Back closes its large view."""
    assert _walk(tmp_path, "view_walk.py", "people.html.j2") == ""


@pytest.mark.parametrize("template", ["quarantine.html.j2", "people.html.j2"])
def test_a_page_is_comfortable_in_both_themes(tmp_path: Path, template: str) -> None:
    """Tab, contrast, no scroll at 1366 px and 200 % zoom, reduced motion (0669)."""
    assert _walk(tmp_path, "comfort_walk.py", template) == ""


@pytest.mark.parametrize("template", ["quarantine.html.j2", "search.html.j2"])
def test_a_running_step_shows_on_the_page_then_its_end(
    tmp_path: Path, template: str
) -> None:
    """A mocked step, running then done: chip, tab title, end said, no error (0661)."""
    assert _walk(tmp_path, "step_walk.py", template) == ""


def test_the_library_shows_few_controls_and_its_menus_open_by_the_keyboard(
    tmp_path: Path,
) -> None:
    """Visible controls at load under the cap; ↓ opens Move ▾, Esc closes it (0665)."""
    assert _walk(tmp_path, "menu_walk.py", "search.html.j2") == ""


def test_the_large_view_preloads_the_next_photo(tmp_path: Path) -> None:
    """300 ms previews: the second → shows at once, 2 requests at most (0675)."""
    assert _walk(tmp_path, "preload_walk.py", "search.html.j2") == ""
