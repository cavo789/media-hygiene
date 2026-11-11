"""The shared page pieces in Chromium: the ask dialog (0663), the busy pieces (0664).

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


def _walk(tmp_path: Path, walk: str) -> str:
    """Run `tests/support/<walk>` on the purge page in the browser; its errors."""
    page = tmp_path / "quarantine.html"
    page.write_text(render_page("quarantine.html.j2"), "utf-8")
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
