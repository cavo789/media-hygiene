"""People's large view steps after Delete; Events prefetch honours data saver."""

from __future__ import annotations

from pathlib import Path

import media_hygiene

_ROOT = Path(media_hygiene.__file__).parent


def test_delete_steps_to_the_next_face_then_the_previous() -> None:
    """Set aside: next face, else the previous, else the view closes (0667)."""
    script = (_ROOT / "people/templates/people_viewer.js.j2").read_text("utf-8")
    assert "viewerNotAside(viewing.at, 1)" in script
    assert "viewerNotAside(viewing.at, -1)" in script
    assert "closeViewer()" in script.split("async function viewerChoice")[1]


def test_events_prefetch_stops_on_data_saver() -> None:
    """Nothing is fetched ahead when the browser asks to save data (0675)."""
    script = (_ROOT / "search/templates/search_events_ahead.js.j2").read_text("utf-8")
    body = script.split("const ahead = async")[1]
    assert body.index("saveData") < body.index("ask(")
