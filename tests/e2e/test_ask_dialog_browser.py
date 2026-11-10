"""The shared ask dialog in Chromium (0663): Esc and the safe button never say yes.

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
_WALK: Final = Path(__file__).parents[1] / "support" / "ask_walk.py"


def test_esc_and_the_safe_button_answer_no(tmp_path: Path) -> None:
    """The purge page's question: Esc, Cancel → no; only the verb button → yes."""
    page = tmp_path / "quarantine.html"
    page.write_text(render_page("quarantine.html.j2"), "utf-8")
    shots = tmp_path / "shots"
    shots.mkdir()
    build_browser()
    run = BrowserRun(
        name="media-hygiene-ask-dialog",
        scripts=(_WALK, page),
        args=("/tmp/quarantine.html",),  # noqa: S108  # inside the browser's container
        network="bridge",  # the script installs playwright first,
    )
    assert run_browser(run, shots) == ""
